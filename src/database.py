"""MongoDB Atlas database layer for MedPath-RAG (users + query history). With local JSON fallback."""
import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017/medpath_rag",
)

# MongoDB client and database
client = None
db = None
users_collection = None
query_history_collection = None

logger = logging.getLogger("MedicalPathologyAPI")


class MockUsersCollection:
    def __init__(self):
        self.file_path = "users_db.json"
        
    def _load(self) -> dict:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
        
    def _save(self, data: dict) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    def find_one(self, filter_dict: dict) -> Optional[dict]:
        data = self._load()
        for username, user in data.items():
            match = True
            for k, v in filter_dict.items():
                if user.get(k) != v:
                    match = False
                    break
            if match:
                return user
        return None
        
    def insert_one(self, user: dict) -> dict:
        data = self._load()
        username = user["username"]
        user_copy = user.copy()
        if "created_at" in user_copy and not isinstance(user_copy["created_at"], str):
            user_copy["created_at"] = user_copy["created_at"].isoformat()
        data[username] = user_copy
        self._save(data)
        return user
        
    def create_index(self, keys, unique=False):
        pass
        
    def count_documents(self, filter_dict: dict) -> int:
        data = self._load()
        if not filter_dict:
            return len(data)
        count = 0
        for username, user in data.items():
            match = True
            for k, v in filter_dict.items():
                if user.get(k) != v:
                    match = False
                    break
            if match:
                count += 1
        return count
        
    def aggregate(self, pipeline: list) -> list:
        data = self._load()
        counts = {}
        for user in data.values():
            role = user.get("role", "user")
            counts[role] = counts.get(role, 0) + 1
        results = []
        for role, count in counts.items():
            results.append({"_id": role, "count": count})
        return results


class MockQueryHistoryCollection:
    def __init__(self):
        self.file_path = "history_db.json"
        
    def _load(self) -> list:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []
        
    def _save(self, data: list) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    def insert_one(self, row: dict) -> dict:
        data = self._load()
        row_copy = row.copy()
        if "timestamp" in row_copy and not isinstance(row_copy["timestamp"], str):
            row_copy["timestamp"] = row_copy["timestamp"].isoformat()
        data.insert(0, row_copy)
        self._save(data)
        return row
        
    def create_index(self, keys, unique=False):
        pass
        
    def find(self, filter_dict: dict = None):
        data = self._load()
        filtered = []
        if filter_dict:
            for row in data:
                match = True
                for k, v in filter_dict.items():
                    # Handle datetime / timestamp comparisons or string checks
                    val = row.get(k)
                    if isinstance(val, datetime):
                        val = val.isoformat()
                    if val != v:
                        match = False
                        break
                if match:
                    filtered.append(row)
        else:
            filtered = data
            
        class FindResult(list):
            def sort(self, key_field, direction=-1):
                reverse_sort = (direction == -1)
                super().sort(key=lambda x: x.get(key_field, ""), reverse=reverse_sort)
                return self
                
            def limit(self, count):
                return FindResult(self[:count])
                
        return FindResult(filtered)
        
    def count_documents(self, filter_dict: dict) -> int:
        data = self._load()
        if not filter_dict:
            return len(data)
            
        is_answered_filter = "answer" in filter_dict
        if is_answered_filter:
            count = 0
            for row in data:
                ans = row.get("answer", "")
                if ans and ans is not None and "couldn't find sufficient" not in ans.lower():
                    count += 1
            return count
            
        count = 0
        for row in data:
            match = True
            for k, v in filter_dict.items():
                if row.get(k) != v:
                    match = False
                    break
            if match:
                count += 1
        return count
        
    def distinct(self, field: str) -> list:
        data = self._load()
        values = set()
        for row in data:
            if field in row:
                values.add(row[field])
        return list(values)
        
    def aggregate(self, pipeline: list) -> list:
        data = self._load()
        
        is_avg = False
        is_category = False
        for step in pipeline:
            if "$group" in step:
                group = step["$group"]
                if "avg_time" in group:
                    is_avg = True
                elif "_id" in group and group["_id"] == "$category":
                    is_category = True
                    
        if is_avg:
            times = [row.get("response_time_sec", 0.0) for row in data if "response_time_sec" in row]
            avg = sum(times) / len(times) if times else 0.0
            return [{"avg_time": avg}]
            
        if is_category:
            counts = {}
            for row in data:
                cat = row.get("category", "general")
                counts[cat] = counts.get(cat, 0) + 1
            results = []
            for cat, count in counts.items():
                results.append({"_id": cat, "count": count})
            return results
            
        return []


class LocalJsonDatabase:
    def __init__(self):
        self.users = MockUsersCollection()
        self.query_history = MockQueryHistoryCollection()
        
    def __getitem__(self, name: str):
        if name == "users":
            return self.users
        elif name == "query_history":
            return self.query_history
        raise KeyError(name)


def init_db() -> None:
    """Initialize MongoDB connection and create indexes, fallback if connection fails."""
    global client, db, users_collection, query_history_collection
    
    try:
        logger.info("Connecting to MongoDB Atlas...")
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        
        # Get database name from URI or use default
        db_name = "medpath_rag"
        if "mongodb+srv://" in MONGODB_URI or "mongodb://" in MONGODB_URI:
            if "/" in MONGODB_URI.split("?")[0]:
                db_name = MONGODB_URI.split("/")[-1].split("?")[0]
        
        db = client[db_name]
        users_collection = db["users"]
        query_history_collection = db["query_history"]
        
        # Create indexes for better performance
        users_collection.create_index([("username", 1)], unique=True)
        users_collection.create_index([("email", 1)])
        
        query_history_collection.create_index([("timestamp", -1)])
        query_history_collection.create_index([("username", 1)])
        query_history_collection.create_index([("category", 1)])
        
        logger.info("MongoDB Atlas connected successfully")
        
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}. Falling back to Local JSON database...")
        db = LocalJsonDatabase()
        users_collection = db["users"]
        query_history_collection = db["query_history"]
        logger.info("Local JSON Database initialized successfully.")


def get_db():
    """Get database instance for dependency injection."""
    global db
    if db is None:
        init_db()
    return db


def history_to_dict(row: dict) -> dict:
    """Convert MongoDB document to dictionary."""
    ts = row.get("timestamp")
    if isinstance(ts, datetime):
        ts = ts.isoformat()
    return {
        "timestamp": ts,
        "username": row.get("username"),
        "question": row.get("question"),
        "category": row.get("category"),
        "answer": row.get("answer"),
        "response_time_sec": row.get("response_time_sec"),
        "sources": row.get("sources", []),
    }


def close_db() -> None:
    """Close MongoDB connection."""
    global client
    if client:
        client.close()

