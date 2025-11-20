"""
Database Helper Functions

MongoDB helper functions ready to use in your backend code.
Import and use these functions in your API endpoints for database operations.
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from typing import Union, Optional, Dict, Any
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

_client = None
db = None

database_url = os.getenv("DATABASE_URL")
database_name = os.getenv("DATABASE_NAME")

if database_url and database_name:
    _client = MongoClient(database_url)
    db = _client[database_name]

# -----------------------------
# Helpers
# -----------------------------

def _to_dict(data: Union[BaseModel, dict]) -> dict:
    if isinstance(data, BaseModel):
        return data.model_dump()
    return dict(data)


def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc
    doc = dict(doc)
    if doc.get("_id") is not None:
        doc["id"] = str(doc["_id"])  # expose as 'id'
        del doc["_id"]
    # Convert datetime to isoformat
    for k, v in list(doc.items()):
        if isinstance(v, datetime):
            doc[k] = v.isoformat()
    return doc

# -----------------------------
# CRUD Operations
# -----------------------------

def create_document(collection_name: str, data: Union[BaseModel, dict]):
    """Insert a single document with timestamp"""
    if db is None:
        raise Exception("Database not available. Check DATABASE_URL and DATABASE_NAME environment variables.")

    data_dict = _to_dict(data)
    data_dict['created_at'] = datetime.now(timezone.utc)
    data_dict['updated_at'] = datetime.now(timezone.utc)

    result = db[collection_name].insert_one(data_dict)
    return str(result.inserted_id)


def get_documents(collection_name: str, filter_dict: Optional[dict] = None, limit: Optional[int] = None):
    """Get documents from collection"""
    if db is None:
        raise Exception("Database not available. Check DATABASE_URL and DATABASE_NAME environment variables.")

    cursor = db[collection_name].find(filter_dict or {})
    if limit:
        cursor = cursor.limit(limit)

    return [serialize_doc(d) for d in cursor]


def get_document_by_id(collection_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
    if db is None:
        raise Exception("Database not available. Check DATABASE_URL and DATABASE_NAME environment variables.")
    try:
        obj_id = ObjectId(doc_id)
    except Exception:
        return None
    doc = db[collection_name].find_one({"_id": obj_id})
    return serialize_doc(doc) if doc else None


def update_document(collection_name: str, doc_id: str, data: Dict[str, Any]) -> bool:
    if db is None:
        raise Exception("Database not available. Check DATABASE_URL and DATABASE_NAME environment variables.")
    try:
        obj_id = ObjectId(doc_id)
    except Exception:
        return False
    data = {k: v for k, v in data.items() if k not in {"_id", "id", "created_at", "updated_at"}}
    data['updated_at'] = datetime.now(timezone.utc)
    res = db[collection_name].update_one({"_id": obj_id}, {"$set": data})
    return res.matched_count > 0


def delete_document(collection_name: str, doc_id: str) -> bool:
    if db is None:
        raise Exception("Database not available. Check DATABASE_URL and DATABASE_NAME environment variables.")
    try:
        obj_id = ObjectId(doc_id)
    except Exception:
        return False
    res = db[collection_name].delete_one({"_id": obj_id})
    return res.deleted_count > 0
