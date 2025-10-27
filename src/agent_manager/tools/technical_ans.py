# tools/tech_info_summary.py
from typing import Optional
from pydantic import BaseModel
from agents import function_tool
from datetime import datetime
from sqlalchemy.orm import Session
from src.db.db import SessionLocal
from src.model.model import Products
import uuid

class TechInfoInput(BaseModel):
    question: str

class TechInfoOutput(BaseModel):
    product_name: Optional[str]
    description: str
    tool_id: str
    timestamp: str


def tech_info_summary(input: TechInfoInput) -> TechInfoOutput:
    """
    Given a question like 'Tell me about the Sentinel R-9 Drone', this tool extracts the product name
    and returns a 3-4 line technical description of the product from the database.
    """
    db: Session = SessionLocal()
    question = input.question.lower()
    
    # Step 1: Match product name
    all_products = db.query(Products).all()
    matched_product = None
    for product in all_products:
        if product.product_name.lower() in question:
            matched_product = product
            break

    if not matched_product:
        return TechInfoOutput(
            product_name=None,
            description="❌ I couldn't identify the product in your question. Please check the name.",
            tool_id=str(uuid.uuid4()),
            timestamp=str(datetime.now())
        )

    # Step 2: Generate 3–4 line summary using description/tech_specs
    product_name = matched_product.product_name
    description = matched_product.descriptions or "No description available."

    # Optional: Use tech_specs to add extra info
    if matched_product.tech_specs:
        bullet_points = []
        for key, value in list(matched_product.tech_specs.items())[:3]:
            bullet_points.append(f"- {key}: {value}")
        extra_info = "\n".join(bullet_points)
        full_description = f"**{product_name}** — {description}\n\nKey Specs:\n{extra_info}"
    else:
        full_description = f"**{product_name}** — {description}"

    return TechInfoOutput(
        product_name=product_name,
        description=full_description,
        tool_id=str(uuid.uuid4()),
        timestamp=str(datetime.now())
    )

get_qa_tool = function_tool(func=tech_info_summary)
