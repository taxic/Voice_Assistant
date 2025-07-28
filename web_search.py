# web_search.py

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional
from config_manager import config
import time
import random

class WebSearcher:
    """Web search and content scraping functionality"""
    
    def __init__(self):
        self.session = requests.Session()
        # Set a realistic user agent to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def search_web(self, query: str, num_results: int = None) -> List[Dict[str, str]]:
        """
        Search the web using DuckDuckGo and return results
        
        Args:
            query: Search query
            num_results: Number of results to return (uses config default if None)
            
        Returns:
            List of dictionaries with 'title', 'url', 'snippet' keys
        """
        if num_results is None:
            num_results = config.get('web_search.max_results', 5)
            
        try:
            # Use DuckDuckGo Instant Answer API for search results
            search_url = "https://html.duckduckgo.com/html/"
            params = {
                'q': query,
                'kl': 'us-en'  # Language and region
            }
            
            print(f"[INFO] Searching web for: '{query}'")
            
            response = self.session.get(
                search_url, 
                params=params, 
                timeout=config.get('web_search.timeout_seconds', 10)
            )
            
            if response.status_code != 200:
                print(f"[ERROR] Search request failed with status {response.status_code}")
                return []
            
            # Parse the HTML response
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Find search result containers
            result_containers = soup.find_all('div', class_='result')
            
            for container in result_containers[:num_results]:
                try:
                    # Extract title and URL
                    title_link = container.find('a', class_='result__a')
                    if not title_link:
                        continue
                        
                    title = title_link.get_text(strip=True)
                    url = title_link.get('href')
                    
                    # Extract snippet
                    snippet_elem = container.find('a', class_='result__snippet')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    if title and url:
                        # Clean up URL (DuckDuckGo sometimes wraps URLs)
                        if url.startswith('/l/?uddg='):
                            # Extract the actual URL from DuckDuckGo's redirect
                            import urllib.parse
                            url = urllib.parse.unquote(url.split('uddg=')[1].split('&')[0])
                        
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet
                        })
                        
                except Exception as e:
                    print(f"[WARN] Error parsing search result: {e}")
                    continue
            
            print(f"[INFO] Found {len(results)} search results")
            return results
            
        except Exception as e:
            print(f"[ERROR] Web search failed: {e}")
            return []
    
    def scrape_content(self, url: str) -> Optional[str]:
        """
        Scrape text content from a webpage
        
        Args:
            url: URL to scrape
            
        Returns:
            Cleaned text content or None if failed
        """
        try:
            print(f"[INFO] Scraping content from: {url}")
            
            response = self.session.get(
                url, 
                timeout=config.get('web_search.scrape_timeout_seconds', 15),
                allow_redirects=True
            )
            
            if response.status_code != 200:
                print(f"[WARN] Failed to fetch {url}: HTTP {response.status_code}")
                return None
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # Try to find main content areas
            main_content = None
            
            # Look for common content containers
            content_selectors = [
                'main', 'article', '.content', '#content', '.post', '.entry',
                '.article-body', '.story-body', '.post-content', '.entry-content'
            ]
            
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            # If no main content found, use body
            if not main_content:
                main_content = soup.find('body')
            
            if not main_content:
                return None
            
            # Extract text
            text = main_content.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit text length
            max_length = config.get('web_search.max_content_length', 3000)
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            return text if text.strip() else None
            
        except Exception as e:
            print(f"[ERROR] Failed to scrape {url}: {e}")
            return None
    
    def search_and_scrape(self, query: str) -> Dict[str, any]:
        """
        Perform web search and scrape content from top results
        
        Args:
            query: Search query
            
        Returns:
            Dictionary with search results and scraped content
        """
        # Get search results
        search_results = self.search_web(query)
        
        if not search_results:
            return {
                'query': query,
                'results': [],
                'scraped_content': [],
                'summary': "No search results found."
            }
        
        # Scrape content from top results
        scraped_content = []
        max_scrape = config.get('web_search.max_scrape_results', 3)
        
        for i, result in enumerate(search_results[:max_scrape]):
            # Add delay to be respectful to servers
            if i > 0:
                time.sleep(random.uniform(1, 3))
            
            content = self.scrape_content(result['url'])
            if content:
                scraped_content.append({
                    'url': result['url'],
                    'title': result['title'],
                    'content': content[:1500] + "..." if len(content) > 1500 else content
                })
        
        return {
            'query': query,
            'results': search_results,
            'scraped_content': scraped_content,
            'summary': f"Found {len(search_results)} results, scraped {len(scraped_content)} pages."
        }
    
    def format_search_context(self, search_data: Dict[str, any]) -> str:
        """
        Format search results for LLM context
        
        Args:
            search_data: Data from search_and_scrape
            
        Returns:
            Formatted string for LLM context
        """
        if not search_data['results']:
            return f"Web search for '{search_data['query']}' returned no results."
        
        context_parts = [f"Web search results for '{search_data['query']}':"]
        
        # Add search result summaries
        context_parts.append("\nSearch Results Overview:")
        for i, result in enumerate(search_data['results'][:5], 1):
            context_parts.append(f"{i}. {result['title']}")
            if result['snippet']:
                context_parts.append(f"   {result['snippet']}")
            context_parts.append(f"   URL: {result['url']}")
        
        # Add scraped content
        if search_data['scraped_content']:
            context_parts.append("\nDetailed Content from Top Results:")
            for i, content in enumerate(search_data['scraped_content'], 1):
                context_parts.append(f"\n--- Content from {content['title']} ---")
                context_parts.append(content['content'])
        
        return "\n".join(context_parts)

# Global instance
web_searcher = WebSearcher()
