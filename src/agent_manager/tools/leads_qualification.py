from typing import Optional
from pydantic import BaseModel
from agents import function_tool
from datetime import datetime
from sqlalchemy.orm import Session
from src.db.db import SessionLocal
from src.model.model import Leads
import uuid
import re


class LeadQualificationInput(BaseModel):
    customer_id: int
    message: str


class LeadQualificationOutput(BaseModel):
    lead_id: Optional[int]
    customer_id: int
    budget_range: Optional[str]
    urgency: str
    qualified: bool
    tool_id: str
    timestamp: str


def lead_qualification(input: LeadQualificationInput) -> LeadQualificationOutput:
    """
    This tool takes a user message like 'I have $20,000 and need it next month',
    extracts the budget and urgency, qualifies the lead, and updates or inserts into the Leads table.
    """

    db: Session = SessionLocal()
    message = input.message.lower()

    # --- Step 1: Extract budget ---
    budget_match = re.search(r"\$?(\d{1,3}(?:,\d{3})*|\d+)(?:\s*(m|k))?", message)
    budget_amount = None
    budget_range = None

    if budget_match:
        amount_str = budget_match.group(1).replace(",", "")
        unit = budget_match.group(2)
        amount = float(amount_str)
        if unit == "m":
            budget_amount = amount * 1_000_000
        elif unit == "k":
            budget_amount = amount * 1_000
        else:
            budget_amount = amount
        budget_range = f"${int(budget_amount - 1000)} - ${int(budget_amount + 1000)}"

    # --- Step 2: Extract urgency ---
    high_keywords = ["asap", "urgent", "next month", "this month", "immediately", "soon"]
    medium_keywords = ["next quarter", "this year", "early next year"]
    urgency = "low"

    if any(word in message for word in high_keywords):
        urgency = "high"
    elif any(word in message for word in medium_keywords):
        urgency = "medium"

    # --- Step 3: Qualification Logic ---
    qualified = bool(budget_amount and budget_amount >= 10_000 and urgency in ["medium", "high"])

    # --- Step 4: Insert or Update into Leads table ---
    existing_lead = db.query(Leads).filter(Leads.customer_id == input.customer_id).first()
    if existing_lead:
        existing_lead.budget_range = budget_range
        existing_lead.urgency = urgency
        existing_lead.qualified = qualified
        db.commit()
        lead_id = existing_lead.lead_id
    else:
        new_lead = Leads(
            customer_id=input.customer_id,
            budget_range=budget_range,
            urgency=urgency,
            qualified=qualified,
        )
        db.add(new_lead)
        db.commit()
        db.refresh(new_lead)
        lead_id = new_lead.lead_id

    return LeadQualificationOutput(
        lead_id=lead_id,
        customer_id=input.customer_id,
        budget_range=budget_range,
        urgency=urgency,
        qualified=qualified,
        tool_id=str(uuid.uuid4()),
        timestamp=str(datetime.now())
    )


get_lead_qual_tool = function_tool(func=lead_qualification)
