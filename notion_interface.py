# notion_interface.py
import requests
import json
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from config_manager import config
import os
from dataclasses import dataclass
from enum import Enum

class NotionError(Exception):
    """Custom exception for Notion-related errors"""
    pass

class CommandType(Enum):
    CREATE_TODO = "create_todo"
    CREATE_NOTE = "create_note"
    SEARCH_PAGES = "search_pages"
    SEARCH_TODOS = "search_todos"
    UPDATE_TODO = "update_todo"
    DELETE_TODO = "delete_todo"
    APPEND_CONTENT = "append_content"
    READ_PAGE = "read_page"
    LIST_TODOS = "list_todos"
    FIND_FREE_TIME = "find_free_time"
    SUMMARIZE_PAGE = "summarize_page"
    ARCHIVE_ITEMS = "archive_items"

@dataclass
class CommandContext:
    """Context information for command execution"""
    last_page_id: Optional[str] = None
    last_search_query: Optional[str] = None
    last_todo_database: Optional[str] = None
    recent_pages: List[str] = None
    conversation_context: Dict[str, Any] = None

    def __post_init__(self):
        if self.recent_pages is None:
            self.recent_pages = []
        if self.conversation_context is None:
            self.conversation_context = {}

class NotionInterface:
    """Enhanced interface for interacting with Notion API with natural language processing"""

    def __init__(self):
        """Initialize Notion interface with API credentials and context management"""
        self.api_token = os.getenv('NOTION_API_TOKEN')
        self.base_url = "https://api.notion.com/v1"
        self.version = "2022-06-28"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Notion-Version": self.version,
            "Content-Type": "application/json"
        }
        self.is_authenticated = self._check_authentication()

        # Get configuration
        self.notion_config = config.get_section('notion', {})
        self.default_database_id = self.notion_config.get('default_database_id')
        self.default_page_id = self.notion_config.get('default_page_id')

        # Context management
        self.context = CommandContext()

        # Command patterns for natural language processing
        self._init_command_patterns()

        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0

        # Cache for performance
        self._page_cache = {}
        self._cache_timeout = 300  # 5 minutes

    def _init_command_patterns(self):
        """Initialize patterns for natural language command processing"""
        self.command_patterns = {
            CommandType.CREATE_TODO: [
                r"(?:create|add|new|make)\s+(?:a\s+)?(?:todo|task|item|reminder)(?:\s+called)?\s*[:""]?\s*(.+?)(?:\s+(?:with\s+)?description\s*[:""]?\s*(.+?))?(?:\s+(?:due\s+)?(?:(today|tomorrow|next\s+\w+|in\s+\d+\s+\w+|on\s+\w+\s+\d+)))?(?:\s+priority\s+(\w+))?$",
                r"(?:todo|task|reminder):\s*(.+?)(?:\s*-\s*(.+?))?(?:\s*\((today|tomorrow|next\s+\w+|in\s+\d+\s+\w+|on\s+\w+\s+\d+)\))?(?:\s*\[(\w+)\])?$",
                r"(?:remind\s+me\s+to\s+)(.+?)(?:\s+(?:on\s+)?(?:(today|tomorrow|next\s+\w+|in\s+\d+\s+\w+|on\s+\w+\s+\d+)))?(?:\s+as\s+(\w+)\s+priority)?$"
            ],
            CommandType.CREATE_NOTE: [
                r"(?:create|add|new|make)\s+(?:a\s+)?(?:note|page|document)(?:\s+called)?\s*[:""]?\s*(.+?)(?:\s+about\s+(.+?))?(?:\s+(?:with\s+)?tags?\s*:?\s*(.+))?$",
                r"(?:note|page):\s*(.+?)(?:\s*-\s*(.+?))?(?:\s*#(\w+(?:\s*#\w+)*))?$"
            ],
            CommandType.SEARCH_PAGES: [
                r"(?:search|find|look\s+for)\s+(?:pages?|notes?|documents?)\s+(?:for|about|with)\s*[:""]?\s*(.+)$",
                r"(?:show|list|display)\s+(?:me\s+)?(?:my\s+)?(?:pages?|notes?|documents?)\s+(?:about|with|containing)\s*[:""]?\s*(.+)$"
            ],
            CommandType.SEARCH_TODOS: [
                r"(?:show|list|display|get)\s+(?:me\s+)?(?:my\s+)?(?:todos?|tasks?|items?)(?:\s+with\s+status\s+(\w+))?(?:\s+(?:called|named|like)\s*[:""]?\s*(.+))?$",
                r"(?:what\s+are\s+)?(?:my\s+)?(?:todos?|tasks?|items?)(?:\s+with\s+status\s+(\w+))?(?:\s+(?:called|named|like)\s*[:""]?\s*(.+))?$"
            ],
            CommandType.UPDATE_TODO: [
                r"(?:update|modify|change|edit)\s+(?:todo|task|item)\s*[:""]?\s*(.+?)\s+(?:to\s+)?(.+?)(?:\s+status\s+(\w+))?(?:\s+priority\s+(\w+))?$",
                r"(?:mark|set)\s+(?:todo|task|item)\s*[:""]?\s*(.+?)\s+(?:as\s+)?(?:complete|completed|done|in\s+progress|cancelled|pending)(?:\s+priority\s+(\w+))?$"
            ],
            CommandType.DELETE_TODO: [
                r"(?:delete|remove|cancel|archive)\s+(?:todo|task|item)\s*[:""]?\s*(.+)$",
                r"(?:get\s+rid\s+of|eliminate|clear)\s+(?:todo|task|item)\s*[:""]?\s*(.+)$"
            ],
            CommandType.APPEND_CONTENT: [
                r"(?:add|append|put)\s+(.+?)\s+(?:to\s+(?:the\s+)?page|in\s+(?:the\s+)?page|on\s+(?:the\s+)?page)\s*[:""]?\s*(.+)$",
                r"(?:update|modify)\s+(?:the\s+)?page\s*[:""]?\s*(.+?)\s+(?:with\s+)?(.+?)$"
            ],
            CommandType.READ_PAGE: [
                r"(?:read|show|get|display)\s+(?:the\s+)?(?:content\s+of\s+)?(?:page|note|document)\s*[:""]?\s*(.+)$",
                r"(?:what(?:'s|\s+is)\s+in\s+(?:the\s+)?page|tell\s+me\s+about\s+(?:the\s+)?page)\s*[:""]?\s*(.+)$"
            ]
        }

    def _check_authentication(self) -> bool:
        """Check if Notion API token is valid with enhanced error handling"""
        if not self.api_token:
            print("[WARN] Notion API token not found. Set NOTION_API_TOKEN environment variable.")
            return False

        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    f"{self.base_url}/users/me",
                    headers=self.headers,
                    timeout=10
                )
                if response.status_code == 200:
                    user_data = response.json()
                    print(f"[INFO] Notion authentication successful for user: {user_data.get('name', 'Unknown')}")
                    return True
                elif response.status_code == 401:
                    print("[ERROR] Invalid Notion API token. Please check your NOTION_API_TOKEN.")
                    return False
                elif response.status_code == 429:
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)
                        print(f"[WARN] Rate limited by Notion API. Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print("[ERROR] Rate limited by Notion API. Please try again later.")
                        return False
                else:
                    print(f"[ERROR] Notion API authentication failed: {response.status_code} - {response.text}")
                    return False
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"[WARN] Network error during authentication. Retrying in {wait_time}s... ({e})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"[ERROR] Failed to authenticate with Notion after {self.max_retries} attempts: {e}")
                    return False
            except Exception as e:
                print(f"[ERROR] Unexpected error during Notion authentication: {e}")
                return False

        return False

    def _make_request(self, method: str, endpoint: str, data: Dict = None, use_cache: bool = False) -> Optional[Dict]:
        """Make a request to Notion API with enhanced error handling and retry logic"""
        if not self.is_authenticated:
            raise NotionError("Not authenticated with Notion API")

        # Check cache for GET requests
        cache_key = None
        if method.upper() == "GET" and use_cache:
            cache_key = f"{method}:{endpoint}:{hash(str(data) if data else '')}"
            if cache_key in self._page_cache:
                cache_entry = self._page_cache[cache_key]
                if time.time() - cache_entry['timestamp'] < self._cache_timeout:
                    return cache_entry['data']
                else:
                    del self._page_cache[cache_key]

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(self.max_retries):
            try:
                if method.upper() == "GET":
                    response = requests.get(url, headers=self.headers, timeout=15, params=data)
                elif method.upper() == "POST":
                    response = requests.post(url, headers=self.headers, json=data, timeout=15)
                elif method.upper() == "PATCH":
                    response = requests.patch(url, headers=self.headers, json=data, timeout=15)
                elif method.upper() == "DELETE":
                    response = requests.delete(url, headers=self.headers, timeout=15)
                else:
                    raise NotionError(f"Unsupported HTTP method: {method}")

                if response.status_code in [200, 201, 204]:
                    result_data = response.json() if response.content else None

                    # Cache successful GET requests
                    if method.upper() == "GET" and use_cache and result_data:
                        self._page_cache[cache_key] = {
                            'data': result_data,
                            'timestamp': time.time()
                        }

                    return result_data
                elif response.status_code == 400:
                    error_msg = "Bad request - please check your parameters"
                    if response.text:
                        try:
                            error_data = response.json()
                            error_msg = error_data.get('message', error_msg)
                        except:
                            pass
                    raise NotionError(f"Bad request: {error_msg}")
                elif response.status_code == 401:
                    raise NotionError("Authentication failed - please check your API token")
                elif response.status_code == 403:
                    raise NotionError("Access forbidden - make sure the page/database is shared with your integration")
                elif response.status_code == 404:
                    raise NotionError("Resource not found - the page or database may have been deleted")
                elif response.status_code == 429:
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)
                        print(f"[WARN] Rate limited by Notion API. Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise NotionError("Rate limited by Notion API. Please try again later.")
                elif response.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)
                        print(f"[WARN] Notion API server error. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise NotionError(f"Notion API server error: {response.status_code}")
                else:
                    raise NotionError(f"Notion API error: {response.status_code} - {response.text}")

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"[WARN] Network error during request. Retrying in {wait_time}s... ({e})")
                    time.sleep(wait_time)
                    continue
                else:
                    raise NotionError(f"Network error after {self.max_retries} attempts: {e}")
            except NotionError:
                raise
            except Exception as e:
                raise NotionError(f"Unexpected error during API request: {e}")

        return None
        
    def _check_authentication(self) -> bool:
        """Check if Notion API token is valid"""
        if not self.api_token:
            print("[WARN] Notion API token not found. Set NOTION_API_TOKEN environment variable.")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/users/me",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"[ERROR] Failed to authenticate with Notion: {e}")
            return False
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Make a request to Notion API with error handling"""
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=15)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=15)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=self.headers, json=data, timeout=15)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"[ERROR] Notion API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"[ERROR] Notion API request failed: {e}")
            return None
    
    def search_pages(self, query: str, page_size: int = 10) -> List[Dict]:
        """Search for pages in Notion workspace"""
        if not self.is_authenticated:
            return []
        
        search_data = {
            "query": query,
            "page_size": page_size,
            "filter": {
                "property": "object",
                "value": "page"
            },
            "sort": {
                "direction": "descending",
                "timestamp": "last_edited_time"
            }
        }
        
        response = self._make_request("POST", "search", search_data)
        if response and "results" in response:
            return response["results"]
        return []
    
    def get_page(self, page_id: str) -> Optional[Dict]:
        """Get a specific page by ID"""
        if not self.is_authenticated:
            return None
        
        return self._make_request("GET", f"pages/{page_id}")
    
    def get_page_content(self, page_id: str) -> Optional[List[Dict]]:
        """Get the content blocks of a page"""
        if not self.is_authenticated:
            return None
        
        response = self._make_request("GET", f"blocks/{page_id}/children")
        if response and "results" in response:
            return response["results"]
        return None
    
    def create_page(self, parent_id: str, title: str, content: str = "", 
                   parent_type: str = "database") -> Optional[str]:
        """Create a new page in Notion"""
        if not self.is_authenticated:
            return None
    
        def parse_natural_language_command(self, text: str) -> Tuple[CommandType, Dict[str, Any]]:
            """
            Parse natural language text to determine command type and extract parameters
            Returns: (command_type, parameters_dict)
            """
            text_lower = text.lower().strip()
    
            # Try to match against each command type's patterns
            for command_type, patterns in self.command_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL)
                    if match:
                        params = self._extract_parameters(command_type, match, text)
                        if params:
                            return command_type, params
    
            # If no pattern matches, try semantic analysis
            return self._semantic_command_analysis(text)
    
        def _extract_parameters(self, command_type: CommandType, match: re.Match, original_text: str) -> Dict[str, Any]:
            """Extract parameters from regex match based on command type"""
            params = {}
    
            if command_type == CommandType.CREATE_TODO:
                # Groups: title, description, due_date, priority
                groups = match.groups()
                if len(groups) >= 1 and groups[0]:
                    params['title'] = groups[0].strip()
                if len(groups) >= 2 and groups[1]:
                    params['description'] = groups[1].strip()
                if len(groups) >= 3 and groups[2]:
                    params['due_date'] = self._parse_due_date(groups[2])
                if len(groups) >= 4 and groups[3]:
                    params['priority'] = groups[3].strip().title()
    
            elif command_type == CommandType.CREATE_NOTE:
                # Groups: title, content, tags
                groups = match.groups()
                if len(groups) >= 1 and groups[0]:
                    params['title'] = groups[0].strip()
                if len(groups) >= 2 and groups[1]:
                    params['content'] = groups[1].strip()
                if len(groups) >= 3 and groups[2]:
                    params['tags'] = [tag.strip() for tag in groups[2].split('#') if tag.strip()]
    
            elif command_type == CommandType.SEARCH_PAGES:
                # Groups: query
                groups = match.groups()
                if len(groups) >= 1 and groups[0]:
                    params['query'] = groups[0].strip()
    
            elif command_type == CommandType.SEARCH_TODOS:
                # Groups: status, query
                groups = match.groups()
                if len(groups) >= 1 and groups[0]:
                    params['status'] = groups[0].strip().title()
                if len(groups) >= 2 and groups[1]:
                    params['query'] = groups[1].strip()
    
            elif command_type == CommandType.UPDATE_TODO:
                # Groups: todo_name, new_value, status, priority
                groups = match.groups()
                if len(groups) >= 1 and groups[0]:
                    params['todo_name'] = groups[0].strip()
                if len(groups) >= 2 and groups[1]:
                    params['new_value'] = groups[1].strip()
                if len(groups) >= 3 and groups[2]:
                    params['status'] = groups[2].strip().title()
                if len(groups) >= 4 and groups[3]:
                    params['priority'] = groups[3].strip().title()
    
            elif command_type == CommandType.DELETE_TODO:
                # Groups: todo_name
                groups = match.groups()
                if len(groups) >= 1 and groups[0]:
                    params['todo_name'] = groups[0].strip()
    
            elif command_type == CommandType.APPEND_CONTENT:
                # Groups: content, page_name
                groups = match.groups()
                if len(groups) >= 1 and groups[0]:
                    params['content'] = groups[0].strip()
                if len(groups) >= 2 and groups[1]:
                    params['page_name'] = groups[1].strip()
    
            elif command_type == CommandType.READ_PAGE:
                # Groups: page_name
                groups = match.groups()
                if len(groups) >= 1 and groups[0]:
                    params['page_name'] = groups[0].strip()
    
            return params
    
        def _parse_due_date(self, date_text: str) -> Optional[str]:
            """Parse natural language date into ISO format"""
            try:
                # Handle relative dates
                date_text_lower = date_text.lower().strip()
    
                if date_text_lower in ['today', 'tonight']:
                    return datetime.now().strftime('%Y-%m-%d')
                elif date_text_lower in ['tomorrow']:
                    return (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                elif 'next' in date_text_lower:
                    # Handle "next Monday", etc.
                    day_map = {
                        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                        'friday': 4, 'saturday': 5, 'sunday': 6
                    }
                    for day_name, day_num in day_map.items():
                        if day_name in date_text_lower:
                            today = datetime.now().weekday()
                            days_ahead = (day_num - today + 7) % 7
                            if days_ahead == 0:
                                days_ahead = 7
                            return (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
                elif 'in' in date_text_lower:
                    # Handle "in 3 days", etc.
                    match = re.search(r'in\s+(\d+)\s+(\w+)', date_text_lower)
                    if match:
                        num = int(match.group(1))
                        unit = match.group(2)
                        if 'day' in unit:
                            return (datetime.now() + timedelta(days=num)).strftime('%Y-%m-%d')
                        elif 'week' in unit:
                            return (datetime.now() + timedelta(weeks=num)).strftime('%Y-%m-%d')
                else:
                    # Try to parse as direct date
                    try:
                        parsed_date = datetime.strptime(date_text_lower, '%Y-%m-%d')
                        return parsed_date.strftime('%Y-%m-%d')
                    except:
                        pass
    
            except Exception as e:
                print(f"[WARN] Failed to parse due date '{date_text}': {e}")
    
            return None
    
        def _semantic_command_analysis(self, text: str) -> Tuple[CommandType, Dict[str, Any]]:
            """Fallback semantic analysis when regex patterns don't match"""
            text_lower = text.lower()
    
            # Simple keyword-based classification
            if any(word in text_lower for word in ['todo', 'task', 'reminder']) and any(word in text_lower for word in ['create', 'add', 'new', 'make']):
                return CommandType.CREATE_TODO, {'title': text}
            elif any(word in text_lower for word in ['note', 'page', 'document']) and any(word in text_lower for word in ['create', 'add', 'new', 'make']):
                return CommandType.CREATE_NOTE, {'title': text}
            elif any(word in text_lower for word in ['search', 'find', 'look for']) and any(word in text_lower for word in ['page', 'pages', 'note', 'notes']):
                return CommandType.SEARCH_PAGES, {'query': text}
            elif any(word in text_lower for word in ['show', 'list', 'get']) and any(word in text_lower for word in ['todo', 'todos', 'task', 'tasks']):
                return CommandType.SEARCH_TODOS, {}
            elif any(word in text_lower for word in ['update', 'modify', 'change', 'edit']) and any(word in text_lower for word in ['todo', 'task']):
                return CommandType.UPDATE_TODO, {'todo_name': text}
            elif any(word in text_lower for word in ['delete', 'remove', 'cancel']) and any(word in text_lower for word in ['todo', 'task']):
                return CommandType.DELETE_TODO, {'todo_name': text}
            elif any(word in text_lower for word in ['add', 'append', 'put']) and any(word in text_lower for word in ['to', 'in', 'on']):
                return CommandType.APPEND_CONTENT, {'content': text}
            elif any(word in text_lower for word in ['read', 'show', 'get']) and any(word in text_lower for word in ['page', 'note', 'content']):
                return CommandType.READ_PAGE, {'page_name': text}
    
            # Default to search if unclear
            return CommandType.SEARCH_PAGES, {'query': text}
    
        def execute_natural_language_command(self, text: str) -> str:
            """
            Execute a natural language command and return user-friendly response
            """
            try:
                command_type, params = self.parse_natural_language_command(text)
    
                # Update context
                self._update_context(command_type, params)
    
                # Execute command based on type
                if command_type == CommandType.CREATE_TODO:
                    return self._execute_create_todo(params)
                elif command_type == CommandType.CREATE_NOTE:
                    return self._execute_create_note(params)
                elif command_type == CommandType.SEARCH_PAGES:
                    return self._execute_search_pages(params)
                elif command_type == CommandType.SEARCH_TODOS:
                    return self._execute_search_todos(params)
                elif command_type == CommandType.UPDATE_TODO:
                    return self._execute_update_todo(params)
                elif command_type == CommandType.DELETE_TODO:
                    return self._execute_delete_todo(params)
                elif command_type == CommandType.APPEND_CONTENT:
                    return self._execute_append_content(params)
                elif command_type == CommandType.READ_PAGE:
                    return self._execute_read_page(params)
                else:
                    return f"Sorry, I couldn't understand that command. I recognized it as a {command_type.value} but couldn't process it properly."
    
            except NotionError as e:
                return f"Notion error: {str(e)}"
            except Exception as e:
                print(f"[ERROR] Failed to execute natural language command: {e}")
                return "Sorry, I encountered an error processing your command. Please try again."
    
        def _update_context(self, command_type: CommandType, params: Dict[str, Any]):
            """Update context based on command execution"""
            if command_type == CommandType.SEARCH_PAGES and 'query' in params:
                self.context.last_search_query = params['query']
    
            # Keep track of recent pages (limit to 10)
            if hasattr(self, '_last_created_page_id'):
                if self._last_created_page_id and len(self.context.recent_pages) < 10:
                    self.context.recent_pages.append(self._last_created_page_id)
                self._last_created_page_id = None
    
        def _execute_create_todo(self, params: Dict[str, Any]) -> str:
            """Execute create todo command"""
            title = params.get('title', 'Untitled Todo')
            description = params.get('description', '')
            due_date = params.get('due_date')
            priority = params.get('priority', 'Medium')
    
            if not self.default_database_id:
                return "Sorry, no default todo database is configured. Please set 'default_database_id' in your config."
    
            try:
                page_id = self.create_todo_item(title, description, due_date, priority)
                if page_id:
                    self._last_created_page_id = page_id
                    return f"✅ Created todo: '{title}'"
                else:
                    return "❌ Failed to create todo item. Please check your database configuration."
            except Exception as e:
                return f"❌ Error creating todo: {str(e)}"
    
        def _execute_create_note(self, params: Dict[str, Any]) -> str:
            """Execute create note command"""
            title = params.get('title', 'Untitled Note')
            content = params.get('content', '')
            tags = params.get('tags', [])
    
            try:
                page_id = self.create_note(title, content, tags)
                if page_id:
                    self._last_created_page_id = page_id
                    tag_text = f" with tags: {', '.join(tags)}" if tags else ""
                    return f"✅ Created note: '{title}'{tag_text}"
                else:
                    return "❌ Failed to create note. Please check your configuration."
            except Exception as e:
                return f"❌ Error creating note: {str(e)}"
    
        def _execute_search_pages(self, params: Dict[str, Any]) -> str:
            """Execute search pages command"""
            query = params.get('query', '')
    
            try:
                pages = self.search_pages(query, page_size=5)
                if not pages:
                    return f"🔍 No pages found matching '{query}'"
    
                response_parts = [f"🔍 Found {len(pages)} pages matching '{query}':"]
                for page in pages:
                    formatted_info = self.format_page_info(page)
                    response_parts.append(f"  {formatted_info}")
    
                return "\n".join(response_parts)
            except Exception as e:
                return f"❌ Error searching pages: {str(e)}"
    
        def _execute_search_todos(self, params: Dict[str, Any]) -> str:
            """Execute search todos command"""
            query = params.get('query', '')
            status = params.get('status')
    
            try:
                todos = self.search_todos(query, status)
                if not todos:
                    filter_text = f" with status '{status}'" if status else ""
                    query_text = f" matching '{query}'" if query else ""
                    return f"📋 No todo items found{query_text}{filter_text}"
    
                response_parts = [f"📋 Found {len(todos)} todo items:"]
                for todo in todos:
                    formatted_info = self.format_database_entry(todo)
                    response_parts.append(f"  {formatted_info}")
    
                return "\n".join(response_parts)
            except Exception as e:
                return f"❌ Error searching todos: {str(e)}"
    
        def _execute_update_todo(self, params: Dict[str, Any]) -> str:
            """Execute update todo command"""
            todo_name = params.get('todo_name', '')
            new_value = params.get('new_value')
            status = params.get('status')
            priority = params.get('priority')
    
            try:
                # First find the todo
                todos = self.search_todos(todo_name)
                if not todos:
                    return f"❌ Couldn't find todo item: '{todo_name}'"
    
                if len(todos) > 1:
                    return f"❌ Found multiple todos matching '{todo_name}'. Please be more specific."
    
                todo = todos[0]
                todo_id = todo.get('id')
    
                if not todo_id:
                    return "❌ Couldn't get todo ID for update"
    
                # Update the todo
                success = self.update_todo_item(todo_id, new_value, status, priority)
                if success:
                    return f"✅ Updated todo: '{todo_name}'"
                else:
                    return "❌ Failed to update todo item"
    
            except Exception as e:
                return f"❌ Error updating todo: {str(e)}"
    
        def _execute_delete_todo(self, params: Dict[str, Any]) -> str:
            """Execute delete todo command"""
            todo_name = params.get('todo_name', '')
    
            try:
                # First find the todo
                todos = self.search_todos(todo_name)
                if not todos:
                    return f"❌ Couldn't find todo item: '{todo_name}'"
    
                if len(todos) > 1:
                    return f"❌ Found multiple todos matching '{todo_name}'. Please be more specific."
    
                todo = todos[0]
                todo_id = todo.get('id')
    
                if not todo_id:
                    return "❌ Couldn't get todo ID for deletion"
    
                # Delete the todo
                success = self.delete_todo_item(todo_id)
                if success:
                    return f"🗑️ Deleted todo: '{todo_name}'"
                else:
                    return "❌ Failed to delete todo item"
    
            except Exception as e:
                return f"❌ Error deleting todo: {str(e)}"
    
        def _execute_append_content(self, params: Dict[str, Any]) -> str:
            """Execute append content command"""
            content = params.get('content', '')
            page_name = params.get('page_name', '')
    
            try:
                # First find the page
                pages = self.search_pages(page_name, page_size=1)
                if not pages:
                    return f"❌ Couldn't find page: '{page_name}'"
    
                page = pages[0]
                page_id = page.get('id')
    
                if not page_id:
                    return "❌ Couldn't get page ID"
    
                # Append content
                success = self.append_to_page(page_id, content)
                if success:
                    return f"✅ Added content to page: '{page_name}'"
                else:
                    return "❌ Failed to add content to page"
    
            except Exception as e:
                return f"❌ Error appending content: {str(e)}"
    
        def _execute_read_page(self, params: Dict[str, Any]) -> str:
            """Execute read page command"""
            page_name = params.get('page_name', '')
    
            try:
                # First find the page
                pages = self.search_pages(page_name, page_size=1)
                if not pages:
                    return f"❌ Couldn't find page: '{page_name}'"
    
                page = pages[0]
                page_id = page.get('id')
    
                if not page_id:
                    return "❌ Couldn't get page ID"
    
                # Get page content
                content = self.get_page_content(page_id)
                if not content:
                    return f"📄 Page '{page_name}' appears to be empty"
    
                # Format content for display
                formatted_content = self._format_page_content(content)
                return f"📄 Content from '{page_name}':\n\n{formatted_content}"
    
            except Exception as e:
                return f"❌ Error reading page: {str(e)}"
    
        def _format_page_content(self, content_blocks: List[Dict]) -> str:
            """Format page content blocks for display"""
            formatted_parts = []
    
            for block in content_blocks:
                block_type = block.get('type', '')
    
                if block_type == 'paragraph':
                    paragraph = block.get('paragraph', {})
                    rich_text = paragraph.get('rich_text', [])
                    text_parts = []
                    for text_obj in rich_text:
                        if text_obj.get('type') == 'text':
                            text_content = text_obj.get('text', {}).get('content', '')
                            text_parts.append(text_content)
                    if text_parts:
                        formatted_parts.append(' '.join(text_parts))
    
                elif block_type.startswith('heading_'):
                    heading = block.get(block_type, {})
                    rich_text = heading.get('rich_text', [])
                    text_parts = []
                    for text_obj in rich_text:
                        if text_obj.get('type') == 'text':
                            text_content = text_obj.get('text', {}).get('content', '')
                            text_parts.append(text_content)
                    if text_parts:
                        heading_text = ' '.join(text_parts)
                        level = int(block_type.split('_')[1])
                        formatted_parts.append(f"{'#' * level} {heading_text}")
    
                elif block_type == 'bulleted_list_item':
                    bullet = block.get('bulleted_list_item', {})
                    rich_text = bullet.get('rich_text', [])
                    text_parts = []
                    for text_obj in rich_text:
                        if text_obj.get('type') == 'text':
                            text_content = text_obj.get('text', {}).get('content', '')
                            text_parts.append(text_content)
                    if text_parts:
                        formatted_parts.append(f"• {' '.join(text_parts)}")
    
                elif block_type == 'numbered_list_item':
                    numbered = block.get('numbered_list_item', {})
                    rich_text = numbered.get('rich_text', [])
                    text_parts = []
                    for text_obj in rich_text:
                        if text_obj.get('type') == 'text':
                            text_content = text_obj.get('text', {}).get('content', '')
                            text_parts.append(text_content)
                    if text_parts:
                        formatted_parts.append(f"1. {' '.join(text_parts)}")
    
            return '\n\n'.join(formatted_parts)
    
        def update_todo_item(self, todo_id: str, new_title: str = None, status: str = None, priority: str = None) -> bool:
            """Update a todo item with new values"""
            if not self.is_authenticated:
                return False
    
            properties = {}
    
            if new_title:
                properties["Name"] = {
                    "title": [
                        {
                            "text": {
                                "content": new_title
                            }
                        }
                    ]
                }
    
            if status:
                properties["Status"] = {
                    "select": {
                        "name": status
                    }
                }
    
            if priority and priority in ["High", "Medium", "Low"]:
                properties["Priority"] = {
                    "select": {
                        "name": priority
                    }
                }
    
            if not properties:
                return False
    
            try:
                response = self._make_request("PATCH", f"pages/{todo_id}", {"properties": properties})
                return response is not None
            except Exception as e:
                print(f"[ERROR] Failed to update todo item: {e}")
                return False
    
        def delete_todo_item(self, todo_id: str) -> bool:
            """Delete/archive a todo item"""
            if not self.is_authenticated:
                return False
    
            try:
                # Archive the page instead of deleting it
                response = self._make_request("PATCH", f"pages/{todo_id}", {
                    "archived": True
                })
                return response is not None
            except Exception as e:
                print(f"[ERROR] Failed to delete todo item: {e}")
                return False
    
        def advanced_search(self, query: str = "", status: str = None, priority: str = None,
                           due_date: str = None, tags: List[str] = None,
                           created_after: str = None, sort_by: str = "created", sort_order: str = "desc") -> List[Dict]:
            """Advanced search with multiple filters"""
            if not self.default_database_id:
                return []
    
            filter_conditions = []
    
            # Text search in title
            if query:
                filter_conditions.append({
                    "property": "Name",
                    "title": {
                        "contains": query
                    }
                })
    
            # Status filter
            if status:
                filter_conditions.append({
                    "property": "Status",
                    "select": {
                        "equals": status
                    }
                })
    
            # Priority filter
            if priority:
                filter_conditions.append({
                    "property": "Priority",
                    "select": {
                        "equals": priority
                    }
                })
    
            # Due date filter
            if due_date:
                try:
                    if due_date == "today":
                        date_filter = datetime.now().strftime("%Y-%m-%d")
                    elif due_date == "tomorrow":
                        date_filter = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                    elif due_date == "overdue":
                        date_filter = datetime.now().strftime("%Y-%m-%d")
                        filter_conditions.append({
                            "property": "Due Date",
                            "date": {
                                "before": date_filter
                            }
                        })
                        filter_conditions = [f for f in filter_conditions if f.get("property") != "Due Date"]
                    else:
                        date_filter = due_date
    
                    if 'date_filter' in locals():
                        filter_conditions.append({
                            "property": "Due Date",
                            "date": {
                                "equals": date_filter
                            }
                        })
                except Exception as e:
                    print(f"[WARN] Failed to parse due date filter: {e}")
    
            # Combine filters
            filter_data = None
            if filter_conditions:
                if len(filter_conditions) == 1:
                    filter_data = filter_conditions[0]
                else:
                    filter_data = {
                        "and": filter_conditions
                    }
    
            # Sorting
            sort_options = []
            if sort_by == "created":
                sort_options.append({
                    "property": "Created time",
                    "direction": sort_order
                })
            elif sort_by == "updated":
                sort_options.append({
                    "property": "Last edited time",
                    "direction": sort_order
                })
            elif sort_by == "due_date":
                sort_options.append({
                    "property": "Due Date",
                    "direction": sort_order
                })
            elif sort_by == "priority":
                sort_options.append({
                    "property": "Priority",
                    "direction": sort_order
                })
    
            return self.query_database(self.default_database_id, filter_data, sort_options)
    
        def get_todos_by_status(self, status: str) -> List[Dict]:
            """Get all todos with a specific status"""
            return self.advanced_search(status=status)
    
        def get_overdue_todos(self) -> List[Dict]:
            """Get all overdue todos"""
            return self.advanced_search(due_date="overdue")
    
        def get_todos_due_today(self) -> List[Dict]:
            """Get all todos due today"""
            return self.advanced_search(due_date="today")
    
        def bulk_update_todos(self, todo_ids: List[str], updates: Dict[str, Any]) -> Dict[str, bool]:
            """Update multiple todos at once"""
            results = {}
    
            for todo_id in todo_ids:
                try:
                    success = self.update_todo_item(todo_id, **updates)
                    results[todo_id] = success
                except Exception as e:
                    print(f"[ERROR] Failed to update todo {todo_id}: {e}")
                    results[todo_id] = False
    
            return results
    
        def bulk_delete_todos(self, todo_ids: List[str]) -> Dict[str, bool]:
            """Delete multiple todos at once"""
            results = {}
    
            for todo_id in todo_ids:
                try:
                    success = self.delete_todo_item(todo_id)
                    results[todo_id] = success
                except Exception as e:
                    print(f"[ERROR] Failed to delete todo {todo_id}: {e}")
                    results[todo_id] = False
    
            return results
    
        def search_content_in_pages(self, query: str, page_size: int = 10) -> List[Dict]:
            """Search for content within pages (not just titles)"""
            if not self.is_authenticated:
                return []
    
            # First get pages matching the query in title
            pages = self.search_pages(query, page_size * 2)  # Get more to filter
    
            matching_pages = []
            for page in pages:
                page_id = page.get('id')
                if not page_id:
                    continue
    
                try:
                    # Get page content
                    content = self.get_page_content(page_id)
                    if content:
                        # Search for query in content
                        page_text = self._extract_text_from_blocks(content).lower()
                        if query.lower() in page_text:
                            matching_pages.append(page)
                            if len(matching_pages) >= page_size:
                                break
                except Exception as e:
                    print(f"[WARN] Failed to search content in page {page_id}: {e}")
                    continue
    
            return matching_pages
    
        def _extract_text_from_blocks(self, blocks: List[Dict]) -> str:
            """Extract all text content from page blocks"""
            text_parts = []
    
            for block in blocks:
                block_type = block.get('type', '')
    
                if block_type == 'paragraph':
                    paragraph = block.get('paragraph', {})
                    rich_text = paragraph.get('rich_text', [])
                    for text_obj in rich_text:
                        if text_obj.get('type') == 'text':
                            text_parts.append(text_obj.get('text', {}).get('content', ''))
    
                elif block_type.startswith('heading_'):
                    heading = block.get(block_type, {})
                    rich_text = heading.get('rich_text', [])
                    for text_obj in rich_text:
                        if text_obj.get('type') == 'text':
                            text_parts.append(text_obj.get('text', {}).get('content', ''))
    
                elif block_type in ['bulleted_list_item', 'numbered_list_item']:
                    list_item = block.get(block_type, {})
                    rich_text = list_item.get('rich_text', [])
                    for text_obj in rich_text:
                        if text_obj.get('type') == 'text':
                            text_parts.append(text_obj.get('text', {}).get('content', ''))
    
            return ' '.join(text_parts)
    
        def summarize_page_content(self, page_id: str, max_length: int = 200) -> str:
            """Create a summary of page content"""
            try:
                content = self.get_page_content(page_id)
                if not content:
                    return "Page appears to be empty"
    
                full_text = self._extract_text_from_blocks(content)
    
                if len(full_text) <= max_length:
                    return full_text
    
                # Simple summarization - take first part and add ellipsis
                summary = full_text[:max_length].rsplit(' ', 1)[0]  # Don't cut words in half
                return summary + "..."
    
            except Exception as e:
                print(f"[ERROR] Failed to summarize page content: {e}")
                return "Unable to summarize page content"
    
        def get_recent_pages(self, limit: int = 5) -> List[Dict]:
            """Get recently modified pages"""
            try:
                # Search with recent sorting
                pages = self.search_pages("", page_size=limit * 2)  # Get more to account for filtering
    
                # Sort by last edited time (this is a simple client-side sort)
                recent_pages = []
                for page in pages:
                    if len(recent_pages) >= limit:
                        break
    
                    last_edited = page.get('last_edited_time', '')
                    if last_edited:
                        recent_pages.append((page, last_edited))
    
                # Sort by last edited time
                recent_pages.sort(key=lambda x: x[1], reverse=True)
    
                return [page for page, _ in recent_pages]
    
            except Exception as e:
                print(f"[ERROR] Failed to get recent pages: {e}")
                return []
    
        def suggest_related_actions(self, current_context: Dict[str, Any]) -> List[str]:
            """Suggest related actions based on current context"""
            suggestions = []
    
            try:
                # If we just created a todo, suggest related actions
                if current_context.get('last_action') == 'create_todo':
                    suggestions.extend([
                        "Show my todos",
                        "Create another todo",
                        "Search for related pages"
                    ])
    
                # If we just searched for something, suggest refinements
                elif current_context.get('last_action') == 'search':
                    last_query = current_context.get('last_query', '')
                    if last_query:
                        suggestions.extend([
                            f"Search todos for '{last_query}'",
                            f"Create a todo about '{last_query}'",
                            "Show overdue todos"
                        ])
    
                # If we have todos, suggest management actions
                if self.default_database_id:
                    try:
                        todos = self.search_todos("", None)
                        if todos:
                            suggestions.extend([
                                "Show overdue todos",
                                "Show todos due today",
                                "List all my todos"
                            ])
                    except:
                        pass
    
                # Always suggest common actions
                suggestions.extend([
                    "Create a new todo",
                    "Search my pages",
                    "Show recent pages"
                ])
    
            except Exception as e:
                print(f"[ERROR] Failed to generate suggestions: {e}")
    
            # Remove duplicates and limit
            return list(set(suggestions))[:5]
    
        def get_context_info(self) -> Dict[str, Any]:
            """Get current context information"""
            return {
                'authenticated': self.is_authenticated,
                'default_database_id': self.default_database_id,
                'default_page_id': self.default_page_id,
                'last_search_query': self.context.last_search_query,
                'recent_pages_count': len(self.context.recent_pages),
                'cache_size': len(self._page_cache)
            }
    
        def get_command_aliases(self) -> Dict[str, List[str]]:
            """Get comprehensive command aliases for natural language processing"""
            return {
                'create_todo': [
                    'create todo', 'add todo', 'new todo', 'make todo', 'create task', 'add task', 'new task', 'make task',
                    'todo:', 'task:', 'reminder:', 'create reminder', 'add reminder', 'set reminder',
                    'remind me to', 'remember to', 'dont forget to', 'make sure to'
                ],
                'create_note': [
                    'create note', 'add note', 'new note', 'make note', 'create page', 'add page', 'new page', 'make page',
                    'note:', 'page:', 'create document', 'add document', 'write note', 'take note'
                ],
                'search_pages': [
                    'search pages', 'find pages', 'look for pages', 'search notes', 'find notes', 'look for notes',
                    'search documents', 'find documents', 'show pages', 'list pages', 'show notes', 'list notes',
                    'what pages do i have', 'find my pages', 'search my pages'
                ],
                'search_todos': [
                    'show todos', 'list todos', 'get todos', 'show tasks', 'list tasks', 'get tasks',
                    'my todos', 'my tasks', 'todo list', 'task list', 'show todo list', 'list my todos',
                    'what are my todos', 'what todos do i have', 'show my todo list'
                ],
                'update_todo': [
                    'update todo', 'modify todo', 'change todo', 'edit todo', 'update task', 'modify task', 'change task',
                    'mark todo', 'set todo', 'update todo status', 'change todo status', 'mark as complete', 'mark as done',
                    'complete todo', 'finish todo', 'done with todo', 'mark complete', 'set as complete'
                ],
                'delete_todo': [
                    'delete todo', 'remove todo', 'cancel todo', 'archive todo', 'delete task', 'remove task', 'cancel task',
                    'get rid of todo', 'eliminate todo', 'clear todo', 'remove from todos', 'delete from todos',
                    'trash todo', 'throw away todo'
                ],
                'append_content': [
                    'add to page', 'append to page', 'add content to', 'append content', 'put in page', 'add to note',
                    'update page', 'modify page', 'edit page', 'change page', 'add text to', 'insert into page'
                ],
                'read_page': [
                    'read page', 'show page', 'get page', 'display page', 'read note', 'show note', 'get note',
                    'what is in page', 'whats in page', 'tell me about page', 'show me the page', 'read the page',
                    'show page content', 'get page content', 'read page content'
                ],
                'list_todos': [
                    'list all todos', 'show all todos', 'all my todos', 'every todo', 'all todos', 'list every todo',
                    'show todo list', 'display all todos', 'get all todos', 'list todos with details'
                ],
                'find_free_time': [
                    'find free time', 'when am i free', 'available time', 'free slots', 'open time', 'available slots',
                    'when can i schedule', 'find time for', 'schedule time', 'book time'
                ],
                'summarize_page': [
                    'summarize page', 'page summary', 'summarize note', 'note summary', 'what is this page about',
                    'give me summary', 'page overview', 'note overview', 'tell me about this page'
                ],
                'archive_items': [
                    'archive todos', 'archive tasks', 'move to archive', 'archive completed', 'clean up todos',
                    'archive old todos', 'move completed to archive', 'archive finished tasks'
                ]
            }
    
        def process_voice_command(self, voice_text: str) -> str:
            """
            Main entry point for processing voice commands with enhanced natural language understanding
            """
            if not self.is_authenticated:
                return "❌ Notion is not connected. Please set up your NOTION_API_TOKEN environment variable and configure your database."
    
            try:
                # Use the enhanced natural language processing
                return self.execute_natural_language_command(voice_text)
    
            except NotionError as e:
                return f"❌ Notion error: {str(e)}"
            except Exception as e:
                print(f"[ERROR] Failed to process voice command: {e}")
                return "❌ Sorry, I encountered an error processing your command. Please try again or check your Notion configuration."
    
        def get_quick_help(self) -> str:
            """Get quick help text for common commands"""
            return """
    🎯 **Common Notion Commands:**
    
    **Creating:**
    • "Create todo: Buy groceries for tomorrow with high priority"
    • "Create note: Meeting notes with tags #work #meeting"
    • "Todo: Call dentist - next Tuesday - high priority"
    
    **Searching:**
    • "Show my todos"
    • "Search pages for vacation"
    • "Show overdue todos"
    • "List todos with status in progress"
    
    **Managing:**
    • "Mark todo 'Buy groceries' as complete"
    • "Delete todo 'Old task'"
    • "Update todo 'Project' to high priority"
    
    **Reading:**
    • "Read page 'Meeting notes'"
    • "Show content of 'Project ideas'"
    • "What is in the page 'Recipes'"
    
    **Tips:**
    • Use natural language - no need for exact commands
    • Include dates like "today", "tomorrow", "next Monday"
    • Specify priority as "high", "medium", or "low"
    • Use quotes for exact phrases in searches
    """
        
        # Prepare parent object
        if parent_type == "database":
            parent = {"database_id": parent_id}
            properties = {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            }
        else:  # page
            parent = {"page_id": parent_id}
            properties = {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            }
        
        page_data = {
            "parent": parent,
            "properties": properties
        }
        
        # Add content if provided
        if content:
            page_data["children"] = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": content
                                }
                            }
                        ]
                    }
                }
            ]
        
        response = self._make_request("POST", "pages", page_data)
        if response:
            return response.get("id")
        return None
    
    def append_to_page(self, page_id: str, content: str, block_type: str = "paragraph") -> bool:
        """Append content to an existing page"""
        if not self.is_authenticated:
            return False
        
        if block_type == "paragraph":
            block_data = {
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": content
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        elif block_type == "heading_2":
            block_data = {
                "children": [
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": content
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        elif block_type == "bulleted_list":
            block_data = {
                "children": [
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": content
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        else:
            return False
        
        response = self._make_request("PATCH", f"blocks/{page_id}/children", block_data)
        return response is not None
    
    def query_database(self, database_id: str, filter_data: Dict = None, 
                      sorts: List[Dict] = None, page_size: int = 10) -> List[Dict]:
        """Query a database with optional filters and sorting"""
        if not self.is_authenticated:
            return []
        
        query_data = {
            "page_size": page_size
        }
        
        if filter_data:
            query_data["filter"] = filter_data
        
        if sorts:
            query_data["sorts"] = sorts
        
        response = self._make_request("POST", f"databases/{database_id}/query", query_data)
        if response and "results" in response:
            return response["results"]
        return []
    
    def create_database_page(self, database_id: str, properties: Dict) -> Optional[str]:
        """Create a new page in a database with specific properties"""
        if not self.is_authenticated:
            return None
        
        page_data = {
            "parent": {
                "database_id": database_id
            },
            "properties": properties
        }
        
        response = self._make_request("POST", "pages", page_data)
        if response:
            return response.get("id")
        return None
    
    def get_database_schema(self, database_id: str) -> Optional[Dict]:
        """Get the schema/structure of a database"""
        if not self.is_authenticated:
            return None
        
        response = self._make_request("GET", f"databases/{database_id}")
        if response and "properties" in response:
            return response["properties"]
        return None
    
    def create_todo_item(self, title: str, description: str = "", 
                        due_date: str = None, priority: str = "Medium") -> Optional[str]:
        """Create a todo item in the default database"""
        if not self.default_database_id:
            return None
        
        properties = {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            },
            "Status": {
                "select": {
                    "name": "Not started"
                }
            }
        }
        
        if description:
            properties["Description"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": description
                        }
                    }
                ]
            }
        
        if due_date:
            try:
                # Parse date string and format for Notion
                date_obj = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                properties["Due Date"] = {
                    "date": {
                        "start": date_obj.strftime("%Y-%m-%d")
                    }
                }
            except:
                pass  # Skip invalid date
        
        if priority in ["High", "Medium", "Low"]:
            properties["Priority"] = {
                "select": {
                    "name": priority
                }
            }
        
        return self.create_database_page(self.default_database_id, properties)
    
    def create_note(self, title: str, content: str, tags: List[str] = None) -> Optional[str]:
        """Create a note page"""
        if not self.default_page_id:
            # Create as a standalone page if no default parent
            return self.create_page(self.default_page_id or "", title, content, "page")
        
        # First create the page
        page_id = self.create_page(self.default_page_id, title, content, "page")
        
        # Add tags if provided and page was created successfully
        if page_id and tags:
            tag_content = f"Tags: {', '.join(tags)}"
            self.append_to_page(page_id, tag_content, "paragraph")
        
        return page_id
    
    def search_todos(self, query: str = "", status: str = None) -> List[Dict]:
        """Search for todo items"""
        if not self.default_database_id:
            return []
        
        filter_conditions = []
        
        if query:
            filter_conditions.append({
                "property": "Name",
                "title": {
                    "contains": query
                }
            })
        
        if status:
            filter_conditions.append({
                "property": "Status",
                "select": {
                    "equals": status
                }
            })
        
        filter_data = None
        if filter_conditions:
            if len(filter_conditions) == 1:
                filter_data = filter_conditions[0]
            else:
                filter_data = {
                    "and": filter_conditions
                }
        
        sorts = [
            {
                "property": "Due Date",
                "direction": "ascending"
            },
            {
                "property": "Priority",
                "direction": "descending"
            }
        ]
        
        return self.query_database(self.default_database_id, filter_data, sorts)
    
    def format_page_info(self, page: Dict) -> str:
        """Format page information for display"""
        try:
            # Get title
            title = "Untitled"
            if "properties" in page:
                # Try different title property names
                for prop_name in ["Name", "Title", "title"]:
                    if prop_name in page["properties"]:
                        prop = page["properties"][prop_name]
                        if prop["type"] == "title" and prop["title"]:
                            title = prop["title"][0]["text"]["content"]
                            break
                        elif prop["type"] == "rich_text" and prop["rich_text"]:
                            title = prop["rich_text"][0]["text"]["content"]
                            break
            
            # Get last edited time
            last_edited = page.get("last_edited_time", "")
            if last_edited:
                try:
                    date_obj = datetime.fromisoformat(last_edited.replace('Z', '+00:00'))
                    last_edited = date_obj.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            return f"• {title} (Last edited: {last_edited})"
        except Exception as e:
            print(f"[WARN] Error formatting page info: {e}")
            return f"• {page.get('id', 'Unknown page')}"
    
    def format_database_entry(self, entry: Dict) -> str:
        """Format database entry for display"""
        try:
            info_parts = []
            
            # Get properties
            properties = entry.get("properties", {})
            
            # Try to get name/title
            name = "Untitled"
            for prop_name in ["Name", "Title", "title"]:
                if prop_name in properties:
                    prop = properties[prop_name]
                    if prop["type"] == "title" and prop["title"]:
                        name = prop["title"][0]["text"]["content"]
                        break
                    elif prop["type"] == "rich_text" and prop["rich_text"]:
                        name = prop["rich_text"][0]["text"]["content"]
                        break
            
            info_parts.append(f"• {name}")
            
            # Add status if available
            if "Status" in properties and properties["Status"]["type"] == "select":
                status = properties["Status"]["select"]
                if status:
                    info_parts.append(f"[{status['name']}]")
            
            # Add due date if available
            if "Due Date" in properties and properties["Due Date"]["type"] == "date":
                due_date = properties["Due Date"]["date"]
                if due_date and due_date["start"]:
                    info_parts.append(f"Due: {due_date['start']}")
            
            # Add priority if available
            if "Priority" in properties and properties["Priority"]["type"] == "select":
                priority = properties["Priority"]["select"]
                if priority:
                    info_parts.append(f"Priority: {priority['name']}")
            
            return " ".join(info_parts)
            
        except Exception as e:
            print(f"[WARN] Error formatting database entry: {e}")
            return f"• {entry.get('id', 'Unknown entry')}"

