import os
from datetime import datetime, timezone


class MongoService:
    def __init__(self):
        self.enabled = False
        uri = os.getenv("MONGODB_URI")
        if not uri:
            print("ℹ MongoDB disabled (MONGODB_URI not set)")
            return
        try:
            from pymongo import MongoClient
            client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            client.admin.command("ping")
            self.db = client[os.getenv("MONGODB_DB", "docagent")]
            self.enabled = True
            print("✓ MongoDB connected")
        except Exception as e:
            print(f"ℹ MongoDB disabled ({e})")

    def save_message(self, session_id: str, role: str, content: str, tools=None) -> None:
        if not self.enabled:
            return
        try:
            self.db.conversations.insert_one({
                "session_id": session_id,
                "role": role,
                "content": content,
                "tools": tools or [],
                "timestamp": datetime.now(timezone.utc),
            })
        except Exception as e:
            print(f"MongoDB write failed: {e}")

    def get_history(self, session_id: str, limit: int = 100) -> list:
        if not self.enabled:
            return []
        cursor = (self.db.conversations
                  .find({"session_id": session_id}, {"_id": 0})
                  .sort("timestamp", 1).limit(limit))
        return list(cursor)


mongo_service = MongoService()
