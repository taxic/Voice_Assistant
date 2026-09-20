# notion_interface.py
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config_manager import config
import os

class NotionError(Exception):
    """Custom exception for Notion-related errors"""
    pass

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

        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0

        # Cache for performance
        self._page_cache = {}
        self._cache_timeout = 300  # 5 minutes

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

