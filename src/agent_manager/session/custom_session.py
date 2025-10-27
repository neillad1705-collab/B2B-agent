from agents.memory import Session
from src.model.model import ChatHistory
from src.db.db import SessionLocal
from typing import List, Optional
import json

class MyCustomSession(Session):
    def __init__(self, session_id: str):
        self.session_id = session_id

    async def get_items(self, limit: Optional[int] = None) -> List[dict]:
        with SessionLocal() as db:
            query = db.query(ChatHistory)\
                      .filter_by(session_id=self.session_id)\
                      .order_by(ChatHistory.id.asc())
            if limit:
                query = query.limit(limit)
            results = query.all()

            items = []
            for item in results:
                if item.role and item.content:
                    items.append({
                        "role": item.role,
                        "content": item.content if isinstance(item.content, str) else json.dumps(item.content)
                    })
                else:
                    #print(f"⚠️ Skipped malformed chat record: id={item.id}, role={item.role}, content={item.content}")
                    pass

            return items

    async def add_items(self, items: List[dict]) -> None:
        with SessionLocal() as db:
            for item in items:
                role = item.get("role")
                content = item.get("content")

                if not role or not content:
                    #print(f"⚠️ Skipping invalid item: {item}")
                    continue

                db.add(ChatHistory(
                    session_id=self.session_id,
                    role=str(role),
                    content=json.dumps(content) if isinstance(content, dict) else str(content)
                ))
            db.commit()

    async def pop_item(self) -> Optional[dict]:
        with SessionLocal() as db:
            item = db.query(ChatHistory)\
                     .filter_by(session_id=self.session_id)\
                     .order_by(ChatHistory.id.desc())\
                     .first()

            if item and item.role and item.content:
                result = {
                    "role": item.role,
                    "content": item.content
                }
                db.delete(item)
                db.commit()
                return result
            elif item:
                #print(f"⚠️ Skipping pop for invalid item: id={item.id}, role={item.role}, content={item.content}")
                db.delete(item)
                db.commit()
            return None

    async def clear_session(self) -> None:
        with SessionLocal() as db:
            db.query(ChatHistory)\
              .filter_by(session_id=self.session_id)\
              .delete()
            db.commit()

    def get_system_context(self) -> str:
        return ""  # You can customize this if needed