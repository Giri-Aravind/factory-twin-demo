"""Chat session persistence — conversations and messages."""
import json
import os
import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import JSONB
from dotenv import load_dotenv

load_dotenv()


class ChatDB:
    def __init__(self):
        self.engine = None

    def _get_engine(self):
        if self.engine is None:
            url = (
                f"postgresql://{os.getenv('CHAT_DB_USER', 'postgres')}:"
                f"{os.getenv('CHAT_DB_PASSWORD', '')}@"
                f"{os.getenv('CHAT_DB_HOST', 'localhost')}:"
                f"{os.getenv('CHAT_DB_PORT', '5432')}/"
                f"{os.getenv('CHAT_DB_NAME', 'factorytwin_chat')}"
            )
            self.engine = create_engine(url, pool_pre_ping=True)
        return self.engine

    def create_tables(self):
        with self._get_engine().connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id VARCHAR(64) PRIMARY KEY,
                    title VARCHAR(255) DEFAULT 'New conversation',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    conversation_id VARCHAR(64) REFERENCES conversations(id) ON DELETE CASCADE,
                    role VARCHAR(16) NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            conn.commit()

    def create_conversation(self):
        cid = str(uuid.uuid4())
        with self._get_engine().connect() as conn:
            conn.execute(text("INSERT INTO conversations (id) VALUES (:id)"), {"id": cid})
            conn.commit()
        return cid

    def add_message(self, conversation_id, role, content, metadata=None):
        # Serialize metadata to JSON string and cast to JSONB in the SQL.
        # Casting :meta::jsonb prevents double-encoding (Postgres parses the string).
        meta_json = json.dumps(metadata or {}, default=str)
        with self._get_engine().connect() as conn:
            conn.execute(
                text(
                    "INSERT INTO messages (conversation_id, role, content, metadata) "
                    "VALUES (:cid, :role, :content, CAST(:meta AS JSONB))"
                ),
                {"cid": conversation_id, "role": role, "content": content, "meta": meta_json},
            )
            if role == "user":
                conn.execute(
                    text(
                        "UPDATE conversations SET title = COALESCE(NULLIF(title, 'New conversation'), :t), "
                        "updated_at = NOW() WHERE id = :id"
                    ),
                    {"t": content[:80], "id": conversation_id},
                )
            conn.commit()

    def get_messages(self, conversation_id, limit=50):
        with self._get_engine().connect() as conn:
            result = conn.execute(
                text(
                    "SELECT role, content, metadata FROM messages "
                    "WHERE conversation_id = :cid ORDER BY created_at DESC LIMIT :lim"
                ),
                {"cid": conversation_id, "lim": limit},
            )
            rows = []
            for r in result.fetchall():
                meta = r[2]
                # SQLAlchemy + JSONB: should already be a dict
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except Exception:
                        meta = {}
                rows.append({"role": r[0], "content": r[1], "metadata": meta or {}})
            rows.reverse()
            return rows

    def get_conversations(self, limit=50):
        with self._get_engine().connect() as conn:
            result = conn.execute(
                text(
                    "SELECT id, title, updated_at FROM conversations "
                    "ORDER BY updated_at DESC LIMIT :lim"
                ),
                {"lim": limit},
            )
            from datetime import datetime, timedelta, timezone
            now = datetime.now(timezone.utc)
            today = now.date()
            yesterday = today - timedelta(days=1)
            week_ago = today - timedelta(days=7)

            convs = []
            for r in result.fetchall():
                ts = r[2]
                if ts is not None and ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts is None:
                    group = "Other"
                elif ts.date() == today:
                    group = "Today"
                elif ts.date() == yesterday:
                    group = "Yesterday"
                elif ts.date() >= week_ago:
                    group = "This week"
                else:
                    group = "Older"
                convs.append({
                    "conversation_id": r[0],
                    "title": r[1],
                    "time_group": group,
                })
            return convs

    def delete_conversation(self, conversation_id):
        with self._get_engine().connect() as conn:
            conn.execute(text("DELETE FROM conversations WHERE id = :id"), {"id": conversation_id})
            conn.commit()

    def verify_connection(self):
        try:
            with self._get_engine().connect() as conn:
                r = conn.execute(text("SELECT COUNT(*) FROM conversations"))
                count = r.fetchone()[0]
                return True, count
        except Exception as e:
            return False, str(e)


chatdb = ChatDB()