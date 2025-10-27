# src/db/models/support_ticket.py
from sqlalchemy import Column, String, Text, Enum, DateTime
from datetime import datetime
from src.db.db import Base  # assuming you have a Base class
import enum
#from pydantic import BaseModel


class TicketCategory(enum.Enum):
    product_issue = "product_issue"
    technical = "technical"
    account = "account"
    billing = "billing"
    feedback = "feedback"
    other = "other"

class TicketPriority(enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

class TicketStatus(enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    ticket_id = Column(String(36), primary_key=True)
    user_id = Column(String(100), nullable=False)
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(Enum(TicketCategory), nullable=False)
    priority = Column(Enum(TicketPriority), default=TicketPriority.medium)
    status = Column(Enum(TicketStatus), default=TicketStatus.open)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
