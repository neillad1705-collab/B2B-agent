import enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, Text, Boolean, Enum, UniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import random
from src.db.db import Base, SessionLocal
from agents import function_tool


# ---------------- ENUM ----------------
class OrderStatus(str, enum.Enum):
    pending = "pending"
    shipped = "shipped"


# ---------------- MODEL ----------------
class Orders(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, nullable=False, unique=True)
    quote_id = Column(Integer, nullable=False, unique=True)
    ship_to_address = Column(Text, nullable=False)
    license_check_done = Column(Boolean, nullable=False, default=True)
    order_status = Column(Enum(OrderStatus), default=OrderStatus.pending)

    __table_args__ = (
        UniqueConstraint('order_id', 'customer_id', 'quote_id', name='unique_order_fields'),
    )


# ---------------- SCHEMA ----------------
class PlaceOrderInput(BaseModel):
    order_id: int = Field(..., description="Unique order ID")
    customer_id: int = Field(..., description="Unique customer ID")
    quote_id: int = Field(..., description="Unique quote ID")
    ship_to_address: str = Field(..., description="Shipping address")
    order_status: Optional[OrderStatus] = Field(OrderStatus.pending, description="Order status (pending/shipped)")


class PlaceOrderOutput(BaseModel):
    success: bool
    message: str


# ---------------- HELPER ----------------
def generate_unique_order_id(db: Session) -> int:
    """Generate a unique 8-digit order_id."""
    while True:
        order_id = random.randint(10_000_000, 99_999_999)  # 8-digit random
        exists = db.query(Orders).filter(Orders.order_id == order_id).first()
        if not exists:
            return order_id


# ---------------- TOOL FUNCTION ----------------
def place_order(data: PlaceOrderInput) -> PlaceOrderOutput:
    """
    Places a new order in the orders table.
    Ensures customer_id and quote_id are unique.
    Generates an 8-digit random order_id.
    """
    db: Session = SessionLocal()
    try:
        # Check for duplicate customer_id or quote_id
        existing = db.query(Orders).filter(
            (Orders.customer_id == data.customer_id) |
            (Orders.quote_id == data.quote_id)
        ).first()
        if existing:
            return PlaceOrderOutput(
                success=False,
                message="Order with same customer_id or quote_id already exists."
            )

        # Generate unique order_id
        order_id = generate_unique_order_id(db)

        # Create new order
        new_order = Orders(
            order_id=order_id,
            customer_id=data.customer_id,
            quote_id=data.quote_id,
            ship_to_address=data.ship_to_address,
            license_check_done=True,
            order_status=data.order_status
        )
        db.add(new_order)
        db.commit()
        return PlaceOrderOutput(success=True, message=f"Order placed successfully with ID {order_id}.")

    except IntegrityError:
        db.rollback()
        return PlaceOrderOutput(success=False, message="Integrity error: Duplicate values detected.")
    except Exception as e:
        db.rollback()
        return PlaceOrderOutput(success=False, message=str(e))
    finally:
        db.close()

order_placement_tool = function_tool(place_order)