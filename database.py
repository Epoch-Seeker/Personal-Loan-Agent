# database.py
import sqlite3
from langchain_core.messages import HumanMessage, AIMessage

DB_NAME = "chat_history.db"

def init_db():
    """Creates the table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            sender_type TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_message(session_id, sender_type, content):
    """Saves a message to the database."""
    # sender_type should be 'human' or 'ai'
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (session_id, sender_type, content) VALUES (?, ?, ?)",
        (session_id, sender_type, content)
    )
    conn.commit()
    conn.close()

def get_chat_history(session_id):
    """Retrieves history as a list of LangChain Message objects."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT sender_type, content FROM messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    messages = []
    for sender_type, content in rows:
        if sender_type == "human":
            messages.append(HumanMessage(content=content))
        elif sender_type == "ai":
            messages.append(AIMessage(content=content))
    
    return messages