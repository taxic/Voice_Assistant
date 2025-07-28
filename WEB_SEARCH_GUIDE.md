# Web Search Integration Guide

Your assistant now has the ability to search the internet and provide informed responses based on real-time web content.

## Features

### 🔍 **Web Search Capabilities**
- Search using DuckDuckGo (privacy-focused search engine)
- Scrape content from top search results
- Intelligent content extraction from web pages
- LLM-powered analysis of search results

### 🧠 **Smart Response Generation**
- Feeds search results into LLM context
- Provides comprehensive answers based on multiple sources
- Cites sources when appropriate
- Handles cases where information is incomplete

## Available Commands

### Voice Commands
You can ask your assistant to search for information using natural language:

- **"Search for [topic]"**
- **"Look up [topic]"**
- **"Find information about [topic]"**
- **"What is [topic]?"**
- **"Tell me about [topic]"**
- **"Research [topic]"**

### Example Usage
- "Search for Python programming tutorials"
- "Look up the weather in Tokyo"
- "What is quantum computing?"
- "Tell me about the latest news in AI"
- "Find information about healthy recipes"
- "Research climate change effects"

## How It Works

### 1. **Intent Recognition**
The assistant recognizes when you want to search for information using:
- Advanced LLM-based intent classification
- Keyword-based fallback patterns
- Context-aware query extraction

### 2. **Web Search Process**
1. **Query Processing**: Cleans and optimizes your search query
2. **Search Execution**: Searches DuckDuckGo for relevant results
3. **Content Scraping**: Extracts detailed content from top results
4. **Context Formation**: Formats information for LLM analysis

### 3. **Response Generation**
- LLM analyzes all gathered information
- Synthesizes comprehensive response
- Includes source citations where relevant
- Provides context and additional insights

## Configuration

### Web Search Settings (`config.json`)

```json
{
  "web_search": {
    "max_results": 5,              // Maximum search results to return
    "max_scrape_results": 3,       // Number of pages to scrape for content
    "timeout_seconds": 10,         // Search request timeout
    "scrape_timeout_seconds": 15,  // Page scraping timeout
    "max_content_length": 3000,    // Maximum content length per page
    "delay_between_requests": 2,   // Delay between scraping requests
    "user_agent": "Mozilla/5.0..." // Browser user agent string
  }
}
```

### Customization Options

#### **Adjust Search Results**
```json
{
  "web_search": {
    "max_results": 10,         // Get more search results
    "max_scrape_results": 5    // Scrape from more sources
  }
}
```

#### **Performance Tuning**
```json
{
  "web_search": {
    "timeout_seconds": 15,           // Longer timeout for slow connections
    "scrape_timeout_seconds": 20,   // More time for complex pages
    "delay_between_requests": 1      // Faster scraping (be respectful)
  }
}
```

## Technical Details

### Search Engine
- **DuckDuckGo**: Privacy-focused, no tracking
- **HTML Parsing**: BeautifulSoup for content extraction
- **Respectful Scraping**: Delays between requests, proper user agents

### Content Processing
- **Smart Extraction**: Identifies main content areas
- **Clean Text**: Removes navigation, ads, and clutter
- **Length Limits**: Prevents overwhelming the LLM context
- **Error Handling**: Graceful fallbacks for failed requests

### LLM Integration
- **Context Formatting**: Structures search data for optimal LLM processing
- **Source Attribution**: Maintains links between content and sources
- **Comprehensive Analysis**: LLM synthesizes information from multiple sources

## Privacy and Ethics

### 🔒 **Privacy Features**
- Uses DuckDuckGo (no user tracking)
- No search history stored permanently
- Respects robots.txt and server policies
- Reasonable request delays to avoid overloading servers

### 🤖 **Ethical Scraping**
- Proper user agent identification
- Reasonable request frequency
- Respects server response codes
- Falls back gracefully on failures

### 📊 **Data Handling**
- Search results used only for current response
- No permanent storage of scraped content
- Memory system may retain interaction summaries
- Configurable content length limits

## Example Interactions

### **Simple Search**
```
User: "Search for Python list comprehensions"
Assistant: "I found several resources about Python list comprehensions. Based on the search results, list comprehensions are a concise way to create lists in Python. Here's what I learned from the documentation and tutorials..."
```

### **Current Events**
```
User: "What's the latest news about renewable energy?"
Assistant: "I searched for recent renewable energy news and found several interesting developments. According to recent articles from [sources], there have been significant advances in solar panel efficiency and new wind farm projects..."
```

### **How-To Queries**
```
User: "How do I bake chocolate chip cookies?"
Assistant: "I found several highly-rated chocolate chip cookie recipes. Based on multiple cooking websites, here's a comprehensive guide combining the best techniques..."
```

## Troubleshooting

### Common Issues

#### **No Search Results**
- Check your internet connection
- Try rephrasing your search query
- Verify the web search configuration

#### **Slow Response Times**
- Increase timeout settings in config
- Reduce `max_scrape_results` for faster responses
- Check network connectivity

#### **Poor Quality Results**
- Try more specific search queries
- Increase `max_results` to get more options
- Use different phrasing or keywords

### Error Messages

#### **"No search results found"**
- Search query may be too specific or contain typos
- DuckDuckGo may be temporarily unavailable
- Network connectivity issues

#### **"Error while searching"**
- Network connectivity problems
- Service temporarily unavailable
- Configuration issues

## Best Practices

### 🎯 **Effective Search Queries**
- Be specific but not overly narrow
- Use clear, descriptive language
- Include relevant keywords
- Ask complete questions

### ⚡ **Performance Tips**
- Use web search for information that changes frequently
- Combine with memory for follow-up questions
- Be patient - comprehensive search takes time

### 🔄 **Memory Integration**
- Search results are saved to memory
- Follow-up questions can reference previous searches
- Build on previous knowledge in conversations

## Configuration Examples

### **Quick Searches**
```json
{
  "web_search": {
    "max_results": 3,
    "max_scrape_results": 1,
    "timeout_seconds": 5
  }
}
```

### **Comprehensive Research**
```json
{
  "web_search": {
    "max_results": 10,
    "max_scrape_results": 5,
    "max_content_length": 5000,
    "scrape_timeout_seconds": 30
  }
}
```

### **Bandwidth Conscious**
```json
{
  "web_search": {
    "max_scrape_results": 1,
    "max_content_length": 1500,
    "delay_between_requests": 3
  }
}
```

## Security Considerations

- Web searches may expose your queries to search engines
- Scraped content comes from third-party websites
- Always verify important information from authoritative sources
- Be cautious with sensitive or personal search queries

## Future Enhancements

Potential improvements being considered:
- Multiple search engine support
- Image search capabilities  
- News-specific search modes
- Scientific paper searches
- Local business information
- Real-time data integration

The web search functionality makes your assistant significantly more capable by providing access to current, comprehensive information from across the internet while maintaining privacy and performance.
