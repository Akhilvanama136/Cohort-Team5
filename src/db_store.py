"""CRUD helpers for MongoDB-backed users and query history."""
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from src.database import history_to_dict

logger = logging.getLogger("MedicalPathologyAPI")

USERS_DB_FILE = "users_db.json"
HISTORY_DB_FILE = "history_db.json"


def get_user_by_username(db, username: str) -> Optional[dict]:
    if db is None:
        return None
    return db["users"].find_one({"username": username})


def username_exists(db, username: str) -> bool:
    if db is None:
        return False
    return db["users"].find_one({"username": username}) is not None


def create_user(db, username: str, email: str, hashed_password: str, role: str) -> dict:
    if db is None:
        raise Exception("Database not available")
    user = {
        "username": username,
        "email": email,
        "hashed_password": hashed_password,
        "role": role,
        "created_at": datetime.utcnow(),
    }
    db["users"].insert_one(user)
    return user


def add_history_entry(db, entry: dict) -> dict:
    if db is None:
        raise Exception("Database not available")
    ts = entry.get("timestamp")
    if isinstance(ts, str):
        timestamp = datetime.fromisoformat(ts)
    else:
        timestamp = ts or datetime.utcnow()

    row = {
        "timestamp": timestamp,
        "username": entry["username"],
        "question": entry["question"],
        "category": entry.get("category") or "general",
        "answer": entry.get("answer"),
        "response_time_sec": entry.get("response_time_sec"),
        "sources": entry.get("sources") or [],
    }
    db["query_history"].insert_one(row)
    return row


def get_all_history(db) -> List[dict]:
    if db is None:
        return []
    rows = db["query_history"].find().sort("timestamp", -1)
    return [history_to_dict(r) for r in rows]


def get_user_history(db, username: str) -> List[dict]:
    if db is None:
        return []
    rows = db["query_history"].find({"username": username}).sort("timestamp", -1)
    return [history_to_dict(r) for r in rows]


def count_users_by_role(db) -> Dict[str, int]:
    if db is None:
        return {"admin": 0, "doctor": 0, "user": 0}
    counts = {"admin": 0, "doctor": 0, "user": 0}
    pipeline = [
        {"$group": {"_id": "$role", "count": {"$sum": 1}}}
    ]
    for result in db["users"].aggregate(pipeline):
        role = result["_id"]
        count = result["count"]
        counts[role] = counts.get(role, 0) + count
    return counts


def count_total_users(db) -> int:
    if db is None:
        return 0
    return db["users"].count_documents({})


def get_history_aggregates(db) -> dict:
    if db is None:
        return {
            "total_queries": 0,
            "avg_response_time_sec": 0.0,
            "unique_query_users": 0,
            "category_counts": {},
            "answer_success_rate_pct": 0.0,
        }
    total = db["query_history"].count_documents({})
    
    # Calculate average response time
    pipeline_avg = [
        {"$group": {"_id": None, "avg_time": {"$avg": "$response_time_sec"}}}
    ]
    avg_result = list(db["query_history"].aggregate(pipeline_avg))
    avg_latency = avg_result[0]["avg_time"] if avg_result else 0.0
    
    # Count unique users
    unique_users = len(db["query_history"].distinct("username"))
    
    # Count by category
    pipeline_category = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]
    category_counts = {}
    for result in db["query_history"].aggregate(pipeline_category):
        cat = result["_id"] or "general"
        category_counts[cat] = result["count"]
    
    # Count answered queries (those with non-empty answers)
    answered = db["query_history"].count_documents({
        "answer": {"$ne": None, "$ne": ""},
        "answer": {"$not": {"$regex": "couldn't find sufficient", "$options": "i"}}
    })
    answer_rate = round((answered / total) * 100, 1) if total else 0.0

    return {
        "total_queries": total,
        "avg_response_time_sec": round(float(avg_latency), 2),
        "unique_query_users": unique_users,
        "category_counts": category_counts,
        "answer_success_rate_pct": answer_rate,
    }


def migrate_json_to_mongodb(db) -> None:
    """One-time import from legacy JSON files if MongoDB collections are empty."""
    if db is None:
        logger.warning("MongoDB database not initialized, skipping migration")
        return
        
    try:
        if db["users"].count_documents({}) > 0:
            return

        if os.path.exists(USERS_DB_FILE):
            with open(USERS_DB_FILE, "r", encoding="utf-8") as f:
                users = json.load(f)
            for data in users.values():
                if username_exists(db, data["username"]):
                    continue
                create_user(
                    db,
                    username=data["username"],
                    email=data["email"],
                    hashed_password=data["hashed_password"],
                    role=data.get("role", "user"),
                )
            logger.info("Migrated %d users from %s", len(users), USERS_DB_FILE)

        if db["query_history"].count_documents({}) == 0 and os.path.exists(HISTORY_DB_FILE):
            with open(HISTORY_DB_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
            for entry in history:
                add_history_entry(db, entry)
            logger.info("Migrated %d history entries from %s", len(history), HISTORY_DB_FILE)
    except Exception as e:
        logger.error(f"Migration error: {e}")
