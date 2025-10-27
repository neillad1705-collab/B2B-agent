# src/db/service/support_ticket_model.py
from src.model.support_ticket import SupportTicket
from src.db.db import SessionLocal

def create_ticket(**kwargs):
    db = SessionLocal()
    try:
        ticket = SupportTicket(**kwargs)
        db.add(ticket)
        db.commit()
    finally:
        db.close()

def get_tickets_by_user(user_id: str):
    db = SessionLocal()
    try:
        return db.query(SupportTicket).filter_by(user_id=user_id).order_by(SupportTicket.created_at.desc()).all()
    finally:
        db.close()
