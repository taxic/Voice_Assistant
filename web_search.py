# web_search.py

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional
from config_manager import config
import time
import random

from duckduckgo_search import DDGS

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

        # Try multiple search approaches
        for attempt in range(3):  # Try up to 3 times
            try:
                print(f"[INFO] Searching web for: '{query}' (attempt {attempt + 1})")
                
                # Add delay between attempts to avoid rate limiting
                if attempt > 0:
                    time.sleep(random.uniform(2, 5))
                
                with DDGS() as ddgs:
                    # Use different backends on retry
                    if attempt == 0:
                        results = list(ddgs.text(query, max_results=num_results))
                    elif attempt == 1:
                        results = list(ddgs.text(query, max_results=num_results, backend="api"))
                    else:
                        results = list(ddgs.text(query, max_results=num_results, backend="html"))

                print(f"[INFO] Found {len(results)} search results")
                
                if results:  # If we got results, return them
                    # Format results to match the expected output
                    formatted_results = []
                    for result in results:
                        formatted_results.append({
                            'title': result.get('title', ''),
                            'url': result.get('href', ''),
                            'snippet': result.get('body', '')
                        })
                    
                    return formatted_results

            except Exception as e:
                print(f"[ERROR] Web search attempt {attempt + 1} failed: {e}")
                if "ratelimit" in str(e).lower() or "429" in str(e):
                    print(f"[INFO] Rate limited, waiting before retry...")
                    time.sleep(random.uniform(5, 10))
                continue
        
        # If all attempts failed, try a fallback method using requests
        print(f"[INFO] All DDGS attempts failed, trying fallback method...")
        return self._fallback_search(query, num_results)
    
    def _fallback_search(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """
        Fallback search method using DuckDuckGo instant answers API
        """
        try:
            # Use instant answers API as fallback
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = self.session.get(
                'https://api.duckduckgo.com/',
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                # Try to extract useful information from the API response
                if data.get('AbstractText'):
                    results.append({
                        'title': data.get('AbstractSource', 'DuckDuckGo'),
                        'url': data.get('AbstractURL', ''),
                        'snippet': data.get('AbstractText', '')
                    })
                
                # Add related topics if available
                if data.get('RelatedTopics'):
                    for topic in data.get('RelatedTopics', [])[:num_results-1]:
                        if isinstance(topic, dict) and topic.get('Text'):
                            results.append({
                                'title': topic.get('FirstURL', '').split('/')[-1].replace('_', ' ') or 'Related Topic',
                                'url': topic.get('FirstURL', ''),
                                'snippet': topic.get('Text', '')
                            })
                
                if results:
                    print(f"[INFO] Fallback search found {len(results)} results")
                    return results
        
        except Exception as e:
            print(f"[ERROR] Fallback search failed: {e}")
        
        # If everything fails, return a message explaining the issue
        return [{
            'title': 'Search temporarily unavailable',
            'url': '',
            'snippet': f'Web search for "{query}" is temporarily unavailable due to rate limiting. Please try again later.'
        }]
    
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
