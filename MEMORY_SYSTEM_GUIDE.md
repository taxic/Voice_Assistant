# Enhanced Memory System Guide

Your assistant now features a sophisticated dual-memory system that provides both contextual awareness and persistent long-term memory.

## Memory Architecture

### 🧠 **Dual Memory System**
- **Short-term Memory**: Current session context and recent interactions
- **Long-term Memory**: Persistent storage of important information
- **Conversation Context**: Active topic tracking and session management

### 📊 **Memory Types**

#### **1. Short-term Memory**
- **Purpose**: Immediate conversation context
- **Storage**: In-memory queue (50 items by default)
- **Duration**: Current session only
- **Content**: Recent user interactions and responses

#### **2. Long-term Memory**
- **Purpose**: Persistent information storage
- **Storage**: SQLite database
- **Duration**: Permanent until manually removed
- **Content**: Important facts, user preferences, significant conversations

#### **3. Conversation Context**
- **Purpose**: Topic tracking and session awareness
- **Features**: Topic detection, conversation summaries, session management
- **Auto-updating**: Tracks conversation flow and topic changes

## Voice Commands

### 📈 **Memory Statistics**
Get information about your memory system:
- **"Show memory stats"**
- **"Memory statistics"**
- **"How much memory do I have?"**
- **"Memory usage"**

### 💾 **Save Information**
Store important information for later:
- **"Remember this: [information]"**
- **"Save this to memory: [information]"**
- **"Don't forget that [information]"**
- **"Keep this in mind: [information]"**

### 🔍 **Search Memory**
Find stored information:
- **"Search my memory for [topic]"**
- **"What did I tell you about [topic]?"**
- **"Find in memory [topic]"**
- **"Recall [topic]"**

### 📝 **Memory Recall**
Reference previous conversations:
- **"What did we talk about yesterday?"**
- **"Remember when I told you about..."**
- **"You said before that..."**
- **"In our previous conversation..."**

## Features

### 🎯 **Intelligent Context Management**

#### **Session Tracking**
- Unique session IDs for each conversation
- Automatic session boundaries
- Context preservation across interactions

#### **Topic Detection**
- Automatic topic identification
- Topic change recognition
- Contextual conversation threading

#### **Importance Scoring**
- 1-10 scale for memory importance
- Automatic promotion to long-term memory (threshold: 7+)
- User-saved items get high importance (8)

### 🔄 **Automatic Memory Management**

#### **Smart Promotion**
Important interactions automatically become long-term memories:
```
User: "Remember my anniversary is March 15th"
→ Automatically saved with importance: 8
→ Promoted to long-term memory
→ Tagged as: ["user_saved", "important"]
```

#### **Context Summarization**
- Periodic conversation summaries
- Topic-based memory organization
- Relationship mapping between memories

#### **Memory Categories**
- `general`: General conversations
- `user_saved`: Explicitly saved information
- `weather`: Weather-related interactions
- `music_play`: Music preferences
- `calendar_add`: Calendar events
- `web_search`: Research topics

### 🏷️ **Tagging and Metadata**

#### **Automatic Tags**
- `user_saved`: Explicitly saved by user
- `important`: High importance items
- `[context_type]`: Based on interaction type

#### **Rich Metadata**
- Timestamps for all memories
- Session associations
- Related item connections
- Category classifications

## Configuration

### Memory Settings (`config.json`)

```json
{
  "memory": {
    "max_recent_interactions": 5,      // LLM context from recent memory
    "contextual_search_limit": 3,      // Items in contextual search
    "short_term_max_items": 50,        // Short-term memory capacity
    "short_term_context_limit": 10,    // Short-term context for LLM
    "long_term_context_limit": 5,      // Long-term context for LLM
    "long_term_threshold": 7,          // Auto-promotion threshold
    "importance_decay_days": 30,       // Importance decay period
    "auto_summarize_threshold": 100    // Auto-summarization trigger
  }
}
```

### Customization Options

#### **Memory Capacity**
```json
{
  "memory": {
    "short_term_max_items": 100,     // More short-term memory
    "long_term_context_limit": 10    // More long-term context
  }
}
```

#### **Importance Thresholds**
```json
{
  "memory": {
    "long_term_threshold": 5,        // Lower threshold = more long-term storage
    "auto_summarize_threshold": 50   // More frequent summarization
  }
}
```

## Technical Details

### 🗄️ **Database Schema**

#### **Interactions Table**
- Short-term memory storage
- User input and assistant responses
- Session tracking and metadata

#### **Long-term Memory Table**
- Persistent information storage
- Structured content with titles
- Category and tag organization

#### **Conversation Contexts Table**
- Session summaries and topics
- Participant tracking
- Conversation length metrics

#### **Memory Relationships Table**
- Inter-memory connections
- Relationship types and strengths
- Temporal associations

### 🔧 **Memory Operations**

#### **Contextual Retrieval**
```python
# Automatic context building for LLM
context = memory.get_contextual_memory(user_query)
# Combines short-term + relevant long-term + conversation context
```

#### **Smart Search**
```python
# Multi-dimensional search
long_term_results = memory.search_long_term_memory(query)
conversation_results = memory.search_conversations(query)
```

#### **Relationship Mapping**
- Automatic relationship detection
- Temporal proximity analysis
- Topic similarity scoring

## Usage Examples

### **Basic Memory Operations**

#### **Saving Information**
```
User: "Remember that my favorite restaurant is Luigi's on Main Street"
Assistant: "I've saved 'my favorite restaurant is Luigi's on Main Street' to your long-term memory in the user_saved category."
```

#### **Retrieving Information**
```
User: "What's my favorite restaurant?"
Assistant: "Based on what you told me before, your favorite restaurant is Luigi's on Main Street."
```

#### **Memory Statistics**
```
User: "Show memory stats"
Assistant: "Here are your memory statistics:
• Short-term memory: 23 items
• Long-term memory: 8 items
• Total interactions: 157
• Current session length: 12 interactions
• Current topic: memory stats

Memory categories:
  - user_saved: 5 items
  - general: 2 items
  - music_play: 1 items"
```

### **Advanced Memory Features**

#### **Contextual Conversations**
```
User: "What music did I ask you to play yesterday?"
Assistant: "I found these music-related memories: Yesterday you asked me to play 'Bohemian Rhapsody' by Queen and 'Hotel California' by Eagles."
```

#### **Cross-session Memory**
```
User: "Continue our discussion about AI ethics"
Assistant: "Based on our previous conversation, we were discussing the importance of transparency in AI systems and you mentioned concerns about bias in machine learning algorithms."
```

### **Memory Management**

#### **Session Management**
- Automatic session boundaries
- Cross-session memory access
- Context preservation

#### **Memory Cleanup**
- Configurable importance decay
- Automatic old memory archival
- User-controlled memory deletion

## Best Practices

### 💡 **Effective Memory Usage**

#### **For Users**
- Be specific when saving information
- Use clear, descriptive language
- Regularly review memory statistics
- Search memories with relevant keywords

#### **For Important Information**
- Use "Remember this:" for critical data
- Provide context with saved information
- Use consistent terminology
- Tag related information similarly

### ⚡ **Performance Optimization**

#### **Memory Efficiency**
- Automatic cleanup of old sessions
- Smart context limiting
- Efficient database indexing
- Configurable memory limits

#### **Search Optimization**
- Multi-keyword search support
- Fuzzy matching capabilities
- Relevance-based ranking
- Category-filtered searches

## Privacy and Data Management

### 🔒 **Data Security**
- Local database storage only
- No external memory services
- User-controlled data retention
- Configurable privacy settings

### 📁 **Data Portability**
- SQLite database format
- JSON export capabilities
- Backup and restore functions
- Cross-platform compatibility

### 🗑️ **Data Cleanup**
- Configurable retention policies
- Manual memory deletion
- Session-based cleanup
- Category-specific management

## Troubleshooting

### Common Issues

#### **Memory Not Saving**
- Check database permissions
- Verify disk space availability
- Review importance thresholds
- Confirm content length requirements

#### **Poor Search Results**
- Use more specific keywords
- Try different search terms
- Check category filters
- Verify memory content exists

#### **Context Not Loading**
- Review configuration limits
- Check database connectivity
- Verify session management
- Restart assistant if needed

### Performance Issues

#### **Slow Memory Operations**
- Reduce context limits in config
- Clean up old memories
- Check database size
- Optimize search queries

#### **High Memory Usage**
- Lower short-term memory limits
- Increase importance thresholds
- Enable automatic cleanup
- Archive old conversations

## Future Enhancements

Planned improvements include:
- Semantic memory search using embeddings
- Automatic memory categorization
- Memory sharing between users
- Advanced relationship mapping
- Natural language memory queries
- Integration with external knowledge bases

The enhanced memory system transforms your assistant from a stateless responder into a truly contextual conversational partner that learns and remembers your preferences, important information, and conversation history.
