# database.py
import sqlite3
from langchain_core.messages import HumanMessage, AIMessage

DB_NAME = "chat_history.db"


# ----------------------------------------------------------
# Create DB table if not exists
# ----------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            sender_type TEXT,  -- human / ai
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


# ----------------------------------------------------------
# Reset session history correctly
# ----------------------------------------------------------
def reset_session(session_id: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # FIXED → correct table name
    cur.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


# ----------------------------------------------------------
# Save chat messages
# ----------------------------------------------------------
def save_message(session_id, sender_type, content):
    """
    sender_type = 'human' or 'ai'
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages(session_id, sender_type, content) VALUES (?, ?, ?)",
        (session_id, sender_type, content)
    )
    conn.commit()
    conn.close()


# ----------------------------------------------------------
# Fetch full chat as LangChain format
# ----------------------------------------------------------
def get_chat_history(session_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT sender_type, content 
        FROM messages 
        WHERE session_id = ? 
        ORDER BY id ASC
    """,(session_id,))

    rows = cur.fetchall()
    conn.close()

    history = []
    for sender, msg in rows:
        history.append(
            HumanMessage(content=msg) if sender=="human" else AIMessage(content=msg)
        )
    return history
