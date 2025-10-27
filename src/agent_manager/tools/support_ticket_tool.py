# src/tools/support_ticket_tool.py
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime
import uuid
from agents import function_tool
from src.db.support_ticket_model import create_ticket, get_tickets_by_user
from src.model.support_ticket import SupportTicket

class SupportTicketInput(BaseModel):
    user_id: str = Field(..., description="ID of the user creating the ticket")
    subject: str = Field(..., min_length=5, description="Subject of the support ticket")
    message: str = Field(..., min_length=10, description="Detailed message")
    category: Literal['product_issue', 'technical', 'account', 'billing', 'feedback', 'other']
    priority: Literal['low', 'medium', 'high'] = 'medium'

class SupportTicketResponse(BaseModel):
    ticket_id: str
    message: str
    timestamp: str

def create_support_ticket(data: SupportTicketInput) -> SupportTicketResponse:
    ticket_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    create_ticket(
        ticket_id=ticket_id,
        user_id=data.user_id,
        subject=data.subject,
        message=data.message,
        category=data.category,
        priority=data.priority,
        status="open",
        created_at=timestamp,
        updated_at=timestamp
    )

    return SupportTicketResponse(
        ticket_id=ticket_id,
        message="Support ticket created successfully. Our team will contact you soon.",
        timestamp=timestamp
    )

def retrieve_support_ticket(user_id: str) -> SupportTicketResponse:
    tickets = get_tickets_by_user(user_id)
    if not tickets:
        return SupportTicketResponse(
            ticket_id="",
            message="No support tickets found.",
            timestamp=datetime.utcnow().isoformat()
        )
    ticket = tickets[0]
    return SupportTicketResponse(
        ticket_id=ticket.ticket_id,
        message="Support ticket retrieved successfully.",
        timestamp=ticket.created_at.isoformat()
    )

create_support_ticket_tool = function_tool(
    create_support_ticket,
)

retrieve_support_ticket_tool = function_tool(
    retrieve_support_ticket,
)
