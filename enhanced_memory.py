# enhanced_memory.py

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
import hashlib
from dataclasses import dataclass
from collections import deque

import numpy as np

from config_manager import config
from ollama_client import embed as ollama_embed

@dataclass
class MemoryItem:
    """Base class for memory items"""
    id: Optional[int] = None
    timestamp: str = ""
    memory_type: str = "general"
    importance: int = 1  # 1-10 scale
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class Interaction(MemoryItem):
    """Short-term interaction memory"""
    user_input: str = ""
    response: str = ""
    context_type: str = "general"
    session_id: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.memory_type = "interaction"
        if self.metadata is None:
            self.metadata = {}

@dataclass
class LongTermMemory(MemoryItem):
    """Long-term persistent memory"""
    title: str = ""
    content: str = ""
    category: str = "general"
    metadata: Dict[str, Any] = None
    related_items: List[int] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.memory_type = "long_term"
        if self.metadata is None:
            self.metadata = {}
        if self.related_items is None:
            self.related_items = []

@dataclass
class ConversationContext(MemoryItem):
    """Context for current conversation"""
    topic: str = ""
    summary: str = ""
    participants: List[str] = None
    conversation_length: int = 0
    
    def __post_init__(self):
        super().__post_init__()
        self.memory_type = "context"
        if self.participants is None:
            self.participants = ["user", "assistant"]

class EnhancedMemory:
    """Enhanced memory system with long-term and short-term capabilities"""
    
    def __init__(self, db_name: str = None):
        if db_name is None:
            db_name = config.get('paths.memory_file', 'enhanced_memory.db')
        
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

        # Short-term memory (current session)
        self.short_term_memory = deque(maxlen=config.get('memory.short_term_max_items', 50))
        self.current_session_id = self._generate_session_id()
        self.conversation_context = ConversationContext()

        # Embedding config for semantic memory search. Kept optional at every
        # call site - if the embed model isn't pulled or Ollama isn't
        # reachable, everything falls back to the old keyword search instead
        # of failing.
        self.embed_model = config.get('llm.embed_model', 'nomic-embed-text')
        self.embed_host = config.get('llm.host', 'http://localhost:11434').rstrip('/')
        self.embed_timeout = config.get('llm.embed_timeout_seconds', 30)
        self.embed_keep_alive = config.get('llm.keep_alive', '10m')

        # Initialize database
        self._create_tables()
        self._migrate_schema()

        # Load recent context on startup
        self._load_recent_context()

        # Best-effort: embed any rows that don't have a vector yet (new
        # columns on an existing DB, or rows saved while Ollama/the embed
        # model was unavailable). No-op once everything is embedded.
        self._backfill_embeddings()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:8]
    
    def _create_tables(self):
        """Create database tables for enhanced memory system"""
        
        # Interactions table (short-term memory)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_input TEXT NOT NULL,
                response TEXT NOT NULL,
                context_type TEXT DEFAULT 'general',
                session_id TEXT,
                importance INTEGER DEFAULT 1,
                tags TEXT,
                metadata TEXT
            )
        """)
        
        # Long-term memory table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS long_term_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                importance INTEGER DEFAULT 1,
                tags TEXT,
                metadata TEXT,
                related_items TEXT
            )
        """)
        
        # Conversation contexts table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_contexts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                session_id TEXT,
                topic TEXT,
                summary TEXT,
                participants TEXT,
                conversation_length INTEGER DEFAULT 0,
                importance INTEGER DEFAULT 1,
                tags TEXT,
                metadata TEXT
            )
        """)
        
        # Memory relationships table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL,
                source_id INTEGER NOT NULL,
                target_type TEXT NOT NULL,
                target_id INTEGER NOT NULL,
                relationship_type TEXT DEFAULT 'related',
                strength REAL DEFAULT 1.0,
                timestamp TEXT NOT NULL
            )
        """)
        
        self.conn.commit()

    def _migrate_schema(self):
        """Add the embedding column to tables that predate semantic search.

        CREATE TABLE IF NOT EXISTS above won't add columns to a table that
        already exists, so this runs an ALTER TABLE for any DB created before
        this change. Safe to call every startup - checks column presence
        first, so it's a no-op once a DB has been migrated.
        """
        for table in ("interactions", "long_term_memory"):
            self.cursor.execute(f"PRAGMA table_info({table})")
            columns = {row[1] for row in self.cursor.fetchall()}
            if "embedding" not in columns:
                print(f"[INFO] Migrating {self.db_name}: adding embedding column to {table}")
                self.cursor.execute(f"ALTER TABLE {table} ADD COLUMN embedding BLOB")
        self.conn.commit()

    def _load_recent_context(self):
        """Load recent conversation context"""
        # Load recent interactions into short-term memory
        self.cursor.execute("""
            SELECT timestamp, user_input, response, context_type, session_id, importance, tags, metadata
            FROM interactions 
            ORDER BY id DESC 
            LIMIT ?
        """, (config.get('memory.short_term_max_items', 50),))
        
        rows = self.cursor.fetchall()
        for row in rows:
            interaction = Interaction(
                timestamp=row[0],
                user_input=row[1],
                response=row[2],
                context_type=row[3],
                session_id=row[4] or "",
                importance=row[5] or 1,
                tags=json.loads(row[6]) if row[6] else [],
                metadata=json.loads(row[7]) if row[7] else {}
            )
            self.short_term_memory.appendleft(interaction)

    # --- Embedding helpers for semantic memory search ---------------------
    # Every call site here is best-effort: on any failure (Ollama down, the
    # embed model not pulled, a bad response) these return None instead of
    # raising, and callers fall back to the old LIKE-based search.

    @staticmethod
    def _batched(items: list, size: int = 64):
        for i in range(0, len(items), size):
            yield items[i:i + size]

    def _embed_texts(self, texts: List[str]) -> Optional[List[bytes]]:
        """Embed a batch of texts, returning one BLOB per text in order, or
        None for the whole batch if embedding isn't available right now."""
        if not texts:
            return []
        try:
            blobs = []
            for chunk in self._batched(texts):
                vectors = ollama_embed(
                    chunk, model=self.embed_model, host=self.embed_host,
                    timeout=self.embed_timeout, keep_alive=self.embed_keep_alive,
                )
                blobs.extend(np.asarray(v, dtype=np.float32).tobytes() for v in vectors)
            return blobs
        except Exception as e:
            print(f"[WARN] Embedding unavailable ({e}). Falling back to keyword search. "
                  f"Run `ollama pull {self.embed_model}` if you haven't.")
            return None

    def _embed_text(self, text: str) -> Optional[bytes]:
        blobs = self._embed_texts([text])
        return blobs[0] if blobs else None

    def _embed_query(self, query: str) -> Optional[np.ndarray]:
        if not query:
            return None
        blob = self._embed_text(query)
        return np.frombuffer(blob, dtype=np.float32) if blob else None

    @staticmethod
    def _rank_by_similarity(query_vector: np.ndarray, rows: List[tuple], limit: int) -> List[tuple]:
        """rows: raw sqlite rows where the LAST column is the embedding BLOB
        (or None). Returns the top `limit` rows by cosine similarity,
        excluding rows with no embedding yet."""
        scored = []
        for row in rows:
            blob = row[-1]
            if not blob:
                continue
            vec = np.frombuffer(blob, dtype=np.float32)
            scored.append((float(np.dot(query_vector, vec)), row))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [row for _, row in scored[:limit]]

    def _backfill_embeddings(self):
        self._backfill_table("interactions", "id", ["user_input", "response"])
        self._backfill_table("long_term_memory", "id", ["title", "content"])

    def _backfill_table(self, table: str, id_col: str, text_cols: List[str]):
        col_list = ", ".join(text_cols)
        self.cursor.execute(f"SELECT {id_col}, {col_list} FROM {table} WHERE embedding IS NULL")
        rows = self.cursor.fetchall()
        if not rows:
            return

        ids = [row[0] for row in rows]
        texts = ["\n".join(str(v) for v in row[1:]) for row in rows]

        blobs = self._embed_texts(texts)
        if blobs is None:
            print(f"[WARN] Skipping embedding backfill for {len(rows)} row(s) in {table} for now.")
            return

        for row_id, blob in zip(ids, blobs):
            self.cursor.execute(f"UPDATE {table} SET embedding = ? WHERE {id_col} = ?", (blob, row_id))
        self.conn.commit()
        print(f"[INFO] Backfilled embeddings for {len(rows)} row(s) in {table}.")

    def save_interaction(self, user_input: str, response: str, context_type: str = "general",
                        importance: int = 1, tags: List[str] = None, metadata: Dict = None):
        """Save an interaction to both short-term and persistent memory"""
        
        if tags is None:
            tags = []
        if metadata is None:
            metadata = {}
        
        # Create interaction object
        interaction = Interaction(
            timestamp=datetime.now().isoformat(),
            user_input=user_input,
            response=response,
            context_type=context_type,
            session_id=self.current_session_id,
            importance=importance,
            tags=tags,
            metadata=metadata
        )
        
        # Add to short-term memory
        self.short_term_memory.append(interaction)

        embedding = self._embed_text(f"{user_input}\n{response}")

        # Save to database
        self.cursor.execute("""
            INSERT INTO interactions
            (timestamp, user_input, response, context_type, session_id, importance, tags, metadata, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interaction.timestamp,
            interaction.user_input,
            interaction.response,
            interaction.context_type,
            interaction.session_id,
            interaction.importance,
            json.dumps(interaction.tags),
            json.dumps(interaction.metadata),
            embedding
        ))

        self.conn.commit()

        # Update conversation context
        self._update_conversation_context(user_input, response, context_type)
    
    def _update_conversation_context(self, user_input: str, response: str, context_type: str):
        """Update the current conversation context"""
        self.conversation_context.conversation_length += 1
        
        # Extract topic if not set or if it's a new topic
        if not self.conversation_context.topic or self._is_topic_change(user_input, context_type):
            self.conversation_context.topic = self._extract_topic(user_input, context_type)
        
        # Update summary (keep last few interactions summary)
        if self.conversation_context.conversation_length % 5 == 0:  # Update every 5 interactions
            self.conversation_context.summary = self._generate_conversation_summary()
    
    def _is_topic_change(self, user_input: str, context_type: str) -> bool:
        """Detect if the conversation topic has changed"""
        # Simple heuristic - can be enhanced with NLP
        topic_change_indicators = [
            "let's talk about", "now about", "switching to", "different topic",
            "change subject", "moving on to", "tell me about"
        ]
        
        user_lower = user_input.lower()
        return any(indicator in user_lower for indicator in topic_change_indicators)
    
    def _extract_topic(self, user_input: str, context_type: str) -> str:
        """Extract conversation topic from user input"""
        if context_type != "general":
            return context_type
        
        # Simple keyword extraction - can be enhanced with NLP
        words = user_input.split()
        if len(words) > 2:
            return " ".join(words[:3])
        return "general conversation"
    
    def _generate_conversation_summary(self) -> str:
        """Generate a summary of recent conversation"""
        if len(self.short_term_memory) < 2:
            return "Brief conversation"
        
        recent_interactions = list(self.short_term_memory)[-5:]  # Last 5 interactions
        topics = set()
        
        for interaction in recent_interactions:
            if interaction.context_type != "general":
                topics.add(interaction.context_type)
        
        if topics:
            return f"Discussion about {', '.join(topics)}"
        else:
            return "General conversation"
    
    def save_long_term_memory(self, title: str, content: str, category: str = "general",
                             importance: int = 5, tags: List[str] = None, 
                             metadata: Dict = None, related_items: List[int] = None):
        """Save information to long-term memory"""
        
        if tags is None:
            tags = []
        if metadata is None:
            metadata = {}
        if related_items is None:
            related_items = []
        
        ltm = LongTermMemory(
            timestamp=datetime.now().isoformat(),
            title=title,
            content=content,
            category=category,
            importance=importance,
            tags=tags,
            metadata=metadata,
            related_items=related_items
        )
        
        embedding = self._embed_text(f"{title}\n{content}")

        self.cursor.execute("""
            INSERT INTO long_term_memory
            (timestamp, title, content, category, importance, tags, metadata, related_items, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ltm.timestamp,
            ltm.title,
            ltm.content,
            ltm.category,
            ltm.importance,
            json.dumps(ltm.tags),
            json.dumps(ltm.metadata),
            json.dumps(ltm.related_items),
            embedding
        ))

        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_short_term_context(self, limit: int = None) -> str:
        """Get short-term memory context for LLM"""
        if limit is None:
            limit = config.get('memory.short_term_context_limit', 10)
        
        recent_interactions = list(self.short_term_memory)[-limit:]
        
        if not recent_interactions:
            return ""
        
        context = "=== Short-term Memory (Current Session) ===\n"
        context += f"Session ID: {self.current_session_id}\n"
        context += f"Current Topic: {self.conversation_context.topic}\n"
        context += f"Conversation Length: {self.conversation_context.conversation_length} interactions\n\n"
        
        for interaction in recent_interactions:
            try:
                dt = datetime.fromisoformat(interaction.timestamp)
                time_str = dt.strftime("%H:%M")
            except:
                time_str = "unknown"
            
            context += f"[{time_str}] User: {interaction.user_input}\n"
            context += f"[{time_str}] Assistant: {interaction.response}\n"
            
            if interaction.tags:
                context += f"   Tags: {', '.join(interaction.tags)}\n"
            context += "\n"
        
        context += "=== End Short-term Memory ===\n\n"
        return context
    
    def get_long_term_context(self, query: str = "", limit: int = None) -> str:
        """Get relevant long-term memory context"""
        if limit is None:
            limit = config.get('memory.long_term_context_limit', 5)
        
        if query:
            # Search for relevant long-term memories
            relevant_memories = self.search_long_term_memory(query, limit)
        else:
            # Get recent important memories
            relevant_memories = self.get_recent_long_term_memory(limit)
        
        if not relevant_memories:
            return ""
        
        context = "=== Long-term Memory (Relevant Information) ===\n"
        
        for memory in relevant_memories:
            try:
                dt = datetime.fromisoformat(memory['timestamp'])
                date_str = dt.strftime("%B %d, %Y")
            except:
                date_str = "unknown date"
            
            context += f"\n[{date_str}] {memory['title']}\n"
            context += f"Category: {memory['category']} | Importance: {memory['importance']}\n"
            context += f"{memory['content']}\n"
            
            if memory['tags']:
                context += f"Tags: {', '.join(memory['tags'])}\n"
        
        context += "\n=== End Long-term Memory ===\n\n"
        return context
    
    @staticmethod
    def _row_to_long_term_dict(row: tuple) -> Dict:
        return {
            'id': row[0],
            'timestamp': row[1],
            'title': row[2],
            'content': row[3],
            'category': row[4],
            'importance': row[5],
            'tags': json.loads(row[6]) if row[6] else [],
            'metadata': json.loads(row[7]) if row[7] else {},
            'related_items': json.loads(row[8]) if row[8] else []
        }

    def search_long_term_memory(self, query: str, limit: int = 10) -> List[Dict]:
        """Search long-term memory semantically, falling back to keyword
        (LIKE) search if embeddings aren't available right now."""
        query_vector = self._embed_query(query)
        if query_vector is not None:
            self.cursor.execute("""
                SELECT id, timestamp, title, content, category, importance, tags, metadata, related_items, embedding
                FROM long_term_memory
            """)
            top_rows = self._rank_by_similarity(query_vector, self.cursor.fetchall(), limit)
            if top_rows:
                return [self._row_to_long_term_dict(row) for row in top_rows]
            # Nothing has an embedding yet (e.g. backfill hasn't run) - fall
            # through to keyword search instead of returning nothing.

        return self._keyword_search_long_term_memory(query, limit)

    def _keyword_search_long_term_memory(self, query: str, limit: int = 10) -> List[Dict]:
        """Original LIKE-based search - used when embeddings are unavailable."""
        search_terms = query.lower().split()

        where_conditions = []
        params = []

        for term in search_terms:
            where_conditions.append("""
                (LOWER(title) LIKE ? OR LOWER(content) LIKE ? OR
                 LOWER(category) LIKE ? OR LOWER(tags) LIKE ?)
            """)
            params.extend([f"%{term}%", f"%{term}%", f"%{term}%", f"%{term}%"])

        where_clause = " AND ".join(where_conditions)

        query_sql = f"""
            SELECT id, timestamp, title, content, category, importance, tags, metadata, related_items
            FROM long_term_memory
            WHERE {where_clause}
            ORDER BY importance DESC, timestamp DESC
            LIMIT ?
        """

        params.append(limit)

        self.cursor.execute(query_sql, params)
        return [self._row_to_long_term_dict(row) for row in self.cursor.fetchall()]

    def get_recent_long_term_memory(self, limit: int = 5) -> List[Dict]:
        """Get recent important long-term memories"""
        self.cursor.execute("""
            SELECT id, timestamp, title, content, category, importance, tags, metadata, related_items
            FROM long_term_memory 
            ORDER BY importance DESC, timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        rows = self.cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'timestamp': row[1],
                'title': row[2],
                'content': row[3],
                'category': row[4],
                'importance': row[5],
                'tags': json.loads(row[6]) if row[6] else [],
                'metadata': json.loads(row[7]) if row[7] else {},
                'related_items': json.loads(row[8]) if row[8] else []
            })
        
        return results
    
    def get_contextual_memory(self, user_query: str, limit: int = None) -> str:
        """Get comprehensive contextual memory for LLM"""
        if limit is None:
            limit = config.get('memory.contextual_search_limit', 5)
        
        context_parts = []
        
        # Add short-term context
        short_term = self.get_short_term_context(limit)
        if short_term:
            context_parts.append(short_term)
        
        # Add relevant long-term context
        long_term = self.get_long_term_context(user_query, limit)
        if long_term:
            context_parts.append(long_term)
        
        # Add conversation context summary
        if self.conversation_context.summary:
            context_parts.append(f"=== Conversation Summary ===\n{self.conversation_context.summary}\n\n")
        
        return "".join(context_parts)
    
    def recall_recent(self, limit: int = 5) -> str:
        """Backward compatibility with old memory interface"""
        return self.get_short_term_context(limit)
    
    @staticmethod
    def _row_to_interaction_dict(row: tuple) -> Dict:
        return {
            'id': row[0],
            'timestamp': row[1],
            'user_input': row[2],
            'response': row[3],
            'context_type': row[4],
            'importance': row[5],
            'tags': json.loads(row[6]) if row[6] else []
        }

    def search_conversations(self, query: str, limit: int = 10) -> List[Dict]:
        """Search historical conversations semantically, falling back to
        keyword (LIKE) search if embeddings aren't available right now."""
        query_vector = self._embed_query(query)
        if query_vector is not None:
            self.cursor.execute("""
                SELECT id, timestamp, user_input, response, context_type, importance, tags, embedding
                FROM interactions
            """)
            top_rows = self._rank_by_similarity(query_vector, self.cursor.fetchall(), limit)
            if top_rows:
                return [self._row_to_interaction_dict(row) for row in top_rows]

        return self._keyword_search_conversations(query, limit)

    def _keyword_search_conversations(self, query: str, limit: int = 10) -> List[Dict]:
        """Original LIKE-based search - used when embeddings are unavailable."""
        search_terms = query.lower().split()

        where_conditions = []
        params = []

        for term in search_terms:
            where_conditions.append("(LOWER(user_input) LIKE ? OR LOWER(response) LIKE ?)")
            params.extend([f"%{term}%", f"%{term}%"])

        where_clause = " AND ".join(where_conditions)

        query_sql = f"""
            SELECT id, timestamp, user_input, response, context_type, importance, tags
            FROM interactions
            WHERE {where_clause}
            ORDER BY importance DESC, timestamp DESC
            LIMIT ?
        """

        params.append(limit)

        self.cursor.execute(query_sql, params)
        return [self._row_to_interaction_dict(row) for row in self.cursor.fetchall()]

    def start_new_session(self):
        """Start a new conversation session"""
        # Save current session context
        if self.conversation_context.conversation_length > 0:
            self._save_conversation_context()
        
        # Reset session
        self.current_session_id = self._generate_session_id()
        self.conversation_context = ConversationContext()
        
        # Keep some short-term memory but mark session boundary
        print(f"[INFO] Started new conversation session: {self.current_session_id}")
    
    def _save_conversation_context(self):
        """Save conversation context to database"""
        self.cursor.execute("""
            INSERT INTO conversation_contexts
            (timestamp, session_id, topic, summary, participants, conversation_length, importance, tags, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            self.current_session_id,
            self.conversation_context.topic,
            self.conversation_context.summary,
            json.dumps(self.conversation_context.participants),
            self.conversation_context.conversation_length,
            self.conversation_context.importance,
            json.dumps(self.conversation_context.tags),
            json.dumps({})
        ))
        
        self.conn.commit()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        # Short-term memory stats
        short_term_count = len(self.short_term_memory)
        
        # Long-term memory stats
        self.cursor.execute("SELECT COUNT(*) FROM long_term_memory")
        long_term_count = self.cursor.fetchone()[0]
        
        # Total interactions
        self.cursor.execute("SELECT COUNT(*) FROM interactions")
        total_interactions = self.cursor.fetchone()[0]
        
        # Categories
        self.cursor.execute("""
            SELECT category, COUNT(*) 
            FROM long_term_memory 
            GROUP BY category 
            ORDER BY COUNT(*) DESC
        """)
        categories = dict(self.cursor.fetchall())
        
        return {
            'short_term_memory_count': short_term_count,
            'long_term_memory_count': long_term_count,
            'total_interactions': total_interactions,
            'current_session_id': self.current_session_id,
            'conversation_length': self.conversation_context.conversation_length,
            'current_topic': self.conversation_context.topic,
            'categories': categories
        }
    
    def close(self):
        """Close database connection"""
        if self.conversation_context.conversation_length > 0:
            self._save_conversation_context()
        self.conn.close()
