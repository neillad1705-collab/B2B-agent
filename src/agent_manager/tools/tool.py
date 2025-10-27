from typing import List
from pydantic import BaseModel
from src.db.db import SessionLocal
from agents import function_tool
from sqlalchemy import text
from typing import List, Optional , Literal
import json

# Define schema for each user row
class UserQueryOutput(BaseModel):
    id: int
    full_name: str
    email: str
    company: str
    user_type: str
    verified: str
    signup_date: str


# Tool that fetches all users and loads the full table data
def get_all_users() -> List[UserQueryOutput]:
    print("🛠️ get_all_users (with raw SQL) tool called")
    try:
        session = SessionLocal()

        # Run raw SQL query
        sql = text("SELECT * FROM user")
        result = session.execute(sql)
        rows = result.fetchall()
        session.close()

        # Convert rows to Pydantic model instances
        return [
            UserQueryOutput(
                id=row[0],
                full_name=row[1],
                email=row[2],
                company=row[3],
                user_type=row[4],
                verified=row[5],
                signup_date=row[6].isoformat() if row[6] else None
            )
            for row in rows
        ]

    except Exception as e:
        print("❌ Error in raw SQL get_all_users:", str(e))
        raise


# Wrap as a tool for agent use
get_all_users_tool = function_tool(
    get_all_users,

    )

####  tools for products

class ProductQueryOutput(BaseModel):
    id: int
    product_name: str
    category: str
    short_description: Optional[str]
    long_description: Optional[str]
    tech_specs: Optional[dict]
    base_price: float
    stock_status: str
    weight: float




def get_all_products() -> List[ProductQueryOutput]:
    print("🛠️ get_all_products (with raw SQL) tool called")
    try:
        session = SessionLocal()
        sql = text("""
            SELECT 
                id, 
                product_name, 
                category, 
                short_description, 
                long_description, 
                tech_specs, 
                base_price, 
                stock_status,
                weight
            FROM products
        """)
        result = session.execute(sql)
        rows = result.fetchall()
        session.close()

        return [
            ProductQueryOutput(
                id=row[0],
                product_name=row[1],
                category=row[2],
                short_description=row[3],
                long_description=row[4],
                tech_specs=json.loads(row[5]) if row[5] else None,  # ✅ fixed
                base_price=float(row[6]),
                stock_status=row[7],
                weight=float(row[8])
            )
            for row in rows
        ]
    except Exception as e:
        print("❌ Error in get_all_products:", str(e))
        raise


get_all_products_tool = function_tool(
    get_all_products,
    #description="Retrieve all product details from the 'products' table, including descriptions, category, specs, price, and stock."
)

#### inventory ###

class InventoryQueryOutput(BaseModel):
    product_id: int
    quantity: int
    last_counted: Optional[str]
    warehouse_location: str


def get_all_inventory() -> List[InventoryQueryOutput]:
    print("🛠️ get_all_inventory (with raw SQL) tool called")
    try:
        session = SessionLocal()

        sql = text("""
            SELECT 
                product_id, 
                quantity_left, 
                last_counted, 
                warehouse_location 
            FROM inventory
        """)
        result = session.execute(sql)
        rows = result.fetchall()
        session.close()

        return [
            InventoryQueryOutput(
                product_id=row[0],
                quantity=row[1],
                last_counted=row[2].isoformat() if row[2] else None,
                warehouse_location=row[3]
            )
            for row in rows
        ]
    except Exception as e:
        print("❌ Error in get_all_inventory:", str(e))
        raise


get_all_inventory_tool = function_tool(
    get_all_inventory,
    #description="Retrieve inventory data for all products, including product_id, quantity left, last counted date, and warehouse location."
)


#### Get all Quoted ####

class QuoteQueryOutput(BaseModel):
    quote_id: int
    customer_id: int
    items: str  # JSON string
    subtotal: float
    tax: float
    total: float
    currency: str
    status: str


def get_all_quotes() -> List[QuoteQueryOutput]:
    print("📋 get_all_quotes (with raw SQL) tool called")
    try:
        session = SessionLocal()
        sql = text("""
            SELECT quote_id, customer_id, items, subtotal, tax, total, currency, status
            FROM quotes
        """)
        rows = session.execute(sql).fetchall()
        session.close()

        return [QuoteQueryOutput(
            quote_id=row[0],
            customer_id=row[1],
            items=row[2],
            subtotal=row[3],
            tax=row[4],
            total=row[5],
            currency=row[6],
            status=row[7]
        ) for row in rows]
    except Exception as e:
        print("❌ Error in get_all_quotes:", str(e))
        raise

get_all_quotes_tool = function_tool(
    get_all_quotes,)


####  Get all orders ###

class OrderQueryOutput(BaseModel):
    order_id: int
    customer_id: int
    quote_id: int
    ship_to_address: str
    license_check_done: bool
    order_status: str


def get_all_orders() -> List[OrderQueryOutput]:
    print("🚚 get_all_orders (with raw SQL) tool called")
    try:
        session = SessionLocal()
        sql = text("""
            SELECT order_id, customer_id, quote_id, ship_to_address, license_check_done, order_status
            FROM orders
        """)
        rows = session.execute(sql).fetchall()
        session.close()

        return [OrderQueryOutput(
            order_id=row[0],
            customer_id=row[1],
            quote_id=row[2],
            ship_to_address=row[3],
            license_check_done=bool(row[4]),
            order_status=row[5]
        ) for row in rows]
    except Exception as e:
        print("❌ Error in get_all_orders:", str(e))
        raise

get_all_orders_tool = function_tool(
    get_all_orders,)


##### leads #####

class LeadQueryOutput(BaseModel):
    lead_id: int
    customer_id: int
    budget_range: str
    project_type: str
    urgency: str
    qualified: bool


def get_all_leads() -> List[LeadQueryOutput]:
    print("📞 get_all_leads (with raw SQL) tool called")
    try:
        session = SessionLocal()
        sql = text("""
            SELECT lead_id, customer_id, budget_range, project_type, urgency, qualified
            FROM leads
        """)
        rows = session.execute(sql).fetchall()
        session.close()

        return [LeadQueryOutput(
            lead_id=row[0],
            customer_id=row[1],
            budget_range=row[2],
            project_type=row[3],
            urgency=row[4],
            qualified=bool(row[5])
        ) for row in rows]
    except Exception as e:
        print("❌ Error in get_all_leads:", str(e))
        raise

get_all_leads_tool = function_tool(
    get_all_leads,)

#### support  Ticket #####

class SupportTicketQueryOutput(BaseModel):
    ticket_id: int
    customer_id: int
    product_id: int
    issue_text: str
    status: str


def get_all_support_tickets() -> List[SupportTicketQueryOutput]:
    print("🎫 get_all_support_tickets (with raw SQL) tool called")
    try:
        session = SessionLocal()
        sql = text("""
            SELECT ticket_id, customer_id, product_id, issue_text, status
            FROM support_ticket
        """)
        rows = session.execute(sql).fetchall()
        session.close()

        return [SupportTicketQueryOutput(
            ticket_id=row[0],
            customer_id=row[1],
            product_id=row[2],
            issue_text=row[3],
            status=row[4]
        ) for row in rows]
    except Exception as e:
        print("❌ Error in get_all_support_tickets:", str(e))
        raise

get_all_support_tickets_tool = function_tool(
    get_all_support_tickets,)


###  feedback ####

class FeedbackInput(BaseModel):
    feedback: Literal["yes", "no"]


# 2. Define the feedback tool function with a clear docstring
def feedback_tool(feedback: Literal["yes", "no"]) -> str:
    """
    Ask the user: "Was this answer helpful?" and take input as either 'yes' or 'no'.
    """
    if feedback == "yes":
        return "👍 Glad I could help! Exiting..."
    else:
        return "💬 I'm here to help. Let's continue the conversation!"


# 3. Register the tool
feedback_tool_func = function_tool(feedback_tool)

#### creating a support ticket ###