from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db import db

router = APIRouter()

# MongoDB collection
history_collection = db["user_history"]

class HistoryRequest(BaseModel):
    uid: str
    source_text: str
    translated_text: str
    source_lang: str
    target_lang: str


@router.post("/add_history")
def add_history(request: HistoryRequest):
    """Save user translation history"""
    doc = {
        "uid": request.uid,
        "source_text": request.source_text,
        "translated_text": request.translated_text,
        "source_lang": request.source_lang,
        "target_lang": request.target_lang,
    }
    history_collection.insert_one(doc)
    return {"message": "✅ History saved successfully"}


@router.get("/get_history/{uid}")
def get_history(uid: str):
    """Fetch translation history for a user"""
    history = list(history_collection.find({"uid": uid}, {"_id": 0}))
    if not history:
        raise HTTPException(status_code=404, detail="No history found")
    return {"history": history}
