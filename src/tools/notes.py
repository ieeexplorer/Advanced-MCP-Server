from datetime import datetime

from src.storage.models import NoteCreate


async def create_note(db, note: NoteCreate) -> dict:
    payload = note.model_dump() if hasattr(note, "model_dump") else note.dict()
    payload.update({
        "id": "note_1",
        "created_at": datetime.utcnow().isoformat(),
    })
    return payload
