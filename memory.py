# memory.py

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re

class Memory:
    def __init__(self, db_name="memory.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_input TEXT,
                response TEXT,
                context_type TEXT DEFAULT 'general'
            )
        """)
        
        # Add context_type column if it doesn't exist (for existing databases)
        try:
            self.cursor.execute("ALTER TABLE interactions ADD COLUMN context_type TEXT DEFAULT 'general'")
            self.conn.commit()
        except sqlite3.OperationalError:
            # Column already exists, ignore the error
            pass
        
        self.conn.commit()

    def save_interaction(self, user_input, response, context_type="general"):
        """Save interaction with optional context type for better categorization"""
        self.cursor.execute(
            "INSERT INTO interactions (timestamp, user_input, response, context_type) VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(), user_input, response, context_type)
        )
        self.conn.commit()

    def recall_recent(self, limit=5) -> str:
        """Get recent interactions formatted as conversation context"""
        self.cursor.execute(
            "SELECT user_input, response, timestamp FROM interactions ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = self.cursor.fetchall()
        rows.reverse()  # oldest to newest
        
        if not rows:
            return ""
        
        context = "\n=== Recent Conversation History ===\n"
        for user_input, response, timestamp in rows:
            # Parse timestamp for better formatting
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%H:%M")
            except:
                time_str = "unknown"
            
            context += f"[{time_str}] User: {user_input}\n"
            context += f"[{time_str}] Assistant: {response}\n"
        
        context += "=== End Recent History ===\n\n"
        return context

    def search_conversations(self, query: str, limit=10) -> List[Dict]:
        """Search for conversations containing specific keywords or phrases"""
        # Simple keyword search - could be enhanced with full-text search
        search_terms = query.lower().split()
        
        # Build dynamic WHERE clause for searching
        where_conditions = []
        params = []
        
        for term in search_terms:
            where_conditions.append("(LOWER(user_input) LIKE ? OR LOWER(response) LIKE ?)")
            params.extend([f"%{term}%", f"%{term}%"])
        
        where_clause = " AND ".join(where_conditions)
        
        query_sql = f"""
            SELECT id, timestamp, user_input, response, context_type 
            FROM interactions 
            WHERE {where_clause}
            ORDER BY timestamp DESC 
            LIMIT ?
        """
        
        params.append(limit)
        
        self.cursor.execute(query_sql, params)
        rows = self.cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'timestamp': row[1],
                'user_input': row[2],
                'response': row[3],
                'context_type': row[4]
            })
        
        return results

    def get_contextual_memory(self, user_query: str, limit=5) -> str:
        """Get relevant memory context based on user query"""
        # First, try to find specific related conversations
        related_conversations = self.search_conversations(user_query, limit)
        
        if related_conversations:
            context = "\n=== Relevant Previous Conversations ===\n"
            for conv in related_conversations:
                try:
                    dt = datetime.fromisoformat(conv['timestamp'])
                    time_str = dt.strftime("%B %d, %H:%M")
                except:
                    time_str = "unknown time"
                
                context += f"\n[{time_str}]\n"
                context += f"User: {conv['user_input']}\n"
                context += f"Assistant: {conv['response']}\n"
            
            context += "=== End Relevant History ===\n\n"
            return context
        
        # Fallback to recent conversations if no specific matches
        return self.recall_recent(limit)

    def get_conversation_summary(self, hours_back=24) -> str:
        """Get a summary of conversations from the last X hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        self.cursor.execute(
            "SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM interactions WHERE timestamp > ?",
            (cutoff_time.isoformat(),)
        )
        
        result = self.cursor.fetchone()
        if result and result[0] > 0:
            count, first_time, last_time = result
            return f"In the last {hours_back} hours, we had {count} interactions from {first_time} to {last_time}."
        else:
            return f"No conversations found in the last {hours_back} hours."

    def close(self):
        """Close database connection"""
        self.conn.close()
