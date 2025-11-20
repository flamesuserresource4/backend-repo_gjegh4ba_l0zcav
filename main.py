import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import (
    create_document,
    get_documents,
    get_document_by_id,
    update_document,
    delete_document,
)
from schemas import schema_summary, get_model_by_collection

app = FastAPI(title="RPG Admin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"ok": True, "service": "RPG Admin API"}


@app.get("/schema")
def get_schema():
    """Expose model JSON schemas for the frontend to generate forms."""
    return schema_summary()


class CreatePayload(BaseModel):
    data: Dict[str, Any]


class UpdatePayload(BaseModel):
    data: Dict[str, Any]


@app.get("/api/{collection}")
def list_documents(collection: str, limit: Optional[int] = 100):
    model = get_model_by_collection(collection)
    if not model:
        raise HTTPException(status_code=404, detail="Unknown collection")
    docs = get_documents(collection, limit=limit)
    return {"items": docs}


@app.get("/api/{collection}/{doc_id}")
def get_document(collection: str, doc_id: str):
    model = get_model_by_collection(collection)
    if not model:
        raise HTTPException(status_code=404, detail="Unknown collection")
    doc = get_document_by_id(collection, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return doc


@app.post("/api/{collection}")
def create(collection: str, payload: CreatePayload):
    model = get_model_by_collection(collection)
    if not model:
        raise HTTPException(status_code=404, detail="Unknown collection")
    # Validate via Pydantic
    obj = model(**payload.data)
    new_id = create_document(collection, obj)
    return {"id": new_id}


@app.put("/api/{collection}/{doc_id}")
def update(collection: str, doc_id: str, payload: UpdatePayload):
    model = get_model_by_collection(collection)
    if not model:
        raise HTTPException(status_code=404, detail="Unknown collection")
    # Validate partial updates loosely by constructing model with existing doc merged
    existing = get_document_by_id(collection, doc_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Not found")
    merged = {**existing, **payload.data}
    # Remove id field before validation
    merged.pop("id", None)
    obj = model(**merged)
    ok = update_document(collection, doc_id, payload.data)
    if not ok:
        raise HTTPException(status_code=400, detail="Update failed")
    return {"ok": True}


@app.delete("/api/{collection}/{doc_id}")
def delete(collection: str, doc_id: str):
    model = get_model_by_collection(collection)
    if not model:
        raise HTTPException(status_code=404, detail="Unknown collection")
    ok = delete_document(collection, doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        from database import db

        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
