from sqlalchemy import Column, Integer, String, Text, Date, Enum, JSON, DECIMAL, ForeignKey , DateTime
from datetime import datetime
from src.db.db import Base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from src.db.db import Base
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime
from sqlalchemy import Column, Integer, String, Float, Enum
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.ext.declarative import declarative_base
import enum
from sqlalchemy import Column, Integer, String, Numeric, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base





class Products(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    product_name = Column(String(100))
    category = Column(Enum('weapon', 'robot', 'firewall'))
    short_description = Column(Text)
    long_description = Column(Text)
    tech_specs = Column(JSON)
    base_price = Column(DECIMAL(10, 2))
    stock_status = Column(Enum('in_stock', 'out_of_stock', 'pre_order'))
    weight = Column(DECIMAL(10, 2))



class Inventory(Base):
    __tablename__ = "inventory"

    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)
    quantity_left = Column(Integer)
    last_counted = Column(Date)
    warehouse_location = Column(String(100))


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    company = Column(String(255), nullable=False)
    user_type = Column(String(50), nullable=False)  # ENUM handling in DB
    verified = Column(String(10), nullable=False)
    #sign_up_date = Column(Date)



Base = declarative_base()

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True)
    role = Column(String(20))  # 'user' or 'assistant'
    content = Column(Text)     # stores message content
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    # 🔽 New fields for intent and sentiment
#     updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class QuoteStatus(enum.Enum):
    generated = "generated"
    sent = "sent"
    accepted = "accepted"

class Quotes(Base):
    __tablename__ = "quotes"

    quote_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, index=True)
    items = Column(Text)  # JSON string
    subtotal = Column(DECIMAL(10, 2))
    tax = Column(DECIMAL(10, 2))
    total = Column(DECIMAL(10, 2))
    currency = Column(String(10))
    status = Column(String(20))  # 'pending', 'accepted', 'rejected'    

class OrderStatusEnum(str, enum.Enum):
    pending = "pending"
    shipped = "shipped"
    delivered = "delivered"


Base = declarative_base()


class Orders(Base):
    __tablename__ = "orders"
    order_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False)
    quote_id = Column(Integer, nullable=False)
    ship_to_address = Column(String, nullable=False)
    license_check_done = Column(Boolean, default=False)
    status = Column(String, default="pending")  # pending → shipped


class Leads(Base):
    __tablename__ = "leads"
    lead_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, index=True)
    budget_range = Column(String(20))  # 'low', 'medium', 'high'
    project_type = Column  
    urgency = Column(String(20))  # 'low', 'medium', 'high'
    qualified = Column(Integer)    

class SupportTicket(Base):
    __tablename__ = "support_ticket"
    ticket_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, index=True)
    product_id = Column(Integer, index=True)
    issue_text = Column(Text)
    status = Column(String(20))  # 'open', 'closed'