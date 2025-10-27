
# perfect main.py  code

from agents import Runner
from agents.run import RunConfig
from src.agent_manager.agent.agent_setup import product_inventory_agent
from src.agent_manager.session.custom_session import MyCustomSession
import asyncio
import uuid

def get_session_id():
    print("🔄 Do you want to resume an old session or start a new one?")
    choice = input("Enter session ID to resume, or press Enter to start a new session: ").strip()

    if choice:
        print(f"✅ Resuming session: {choice}\n")
        return choice
    else:
        new_id = str(uuid.uuid4())  # Or you can use timestamp if preferred
        print(f"🆕 Starting new session: {new_id}\n")
        return new_id

async def main():
    print("💬 Chat started with Product Inventory Agent! Type 'exit' to quit.\n")

    session_id = get_session_id()
    session = MyCustomSession(session_id)
    run_config = RunConfig(tracing_disabled=True)

    while True:
        user_input = input("you: ")
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Session ended.")
            break

        result = await Runner.run(
            product_inventory_agent,
            input=user_input,
            session=session,
            run_config=run_config
        )
        print(f"🤖 agent: {result.final_output}\n")

if __name__ == "__main__":
    asyncio.run(main())




### other codes 




from agents import Runner
from agents.run import RunConfig
from agent_manager.agent.agent_setup import product_inventory_agent
from agent_manager.session.custom_session import MyCustomSession
import asyncio

async def main():
    print("💬 Chat started with Product Inventory Agent! Type 'exit' to quit.\n")
    run_config = RunConfig(tracing_disabled=True)
    session = MyCustomSession("session_123")

    # 🧠 General personality + context
    base_prompt = (
        "You are a helpful AI assistant who knows everything about our product inventory system. "
        "You can answer questions about products, inventory, and registered users. "
        "You are also friendly and conversational if the question is casual."
    )

    # 👇 Combine with DB context
    #system_instruction = f"{base_prompt}\n\n{session.get_system_context()}"

    while True:
        user_input = input("you: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        result = await Runner.run(
            product_inventory_agent,
            input=user_input,
            session=session,
            #system_instruction=base_prompt,
            run_config=run_config
        )
        print(f"{product_inventory_agent.name}: {result.final_output}\n")
        #print(f"🤖 agent: {result.final_output}\n")

if __name__ == "__main__":
    asyncio.run(main())



##### custom session #####

# src/agent_manager/session/session.py

import os
import json
import pymysql
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel
from agents.memory import Session
from agents.tool import function_tool
from src.db.db import SessionLocal
from src.model.model import ChatHistory

load_dotenv()

# ---------- Database Configuration ----------

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "neel1705"),
    "database": os.getenv("DB_NAME", "b2b"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "cursorclass": pymysql.cursors.DictCursor,
}

# ---------- Pydantic Schemas ----------

class ProductInfo(BaseModel):
    product_name: str
    category: str
    short_description: str
    base_price: float
    stock_status: str

class InventoryInfo(BaseModel):
    product_id: int
    quantity_left: int
    warehouse_location: str
    last_counted: str

class UserInfo(BaseModel):
    id: int
    full_name: str
    email: str
    company: str
    user_type: str
    verified: str

# ---------- Database Utility Functions ----------

def fetch_all_products() -> List[ProductInfo]:
    try:
        with pymysql.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT product_name, category, short_description, base_price, stock_status FROM products"
                )
                rows = cursor.fetchall()
                return [ProductInfo(**row) for row in rows]
    except Exception as e:
        print(f"❌ fetch_all_products error: {e}")
        return []

def fetch_inventory_info() -> List[InventoryInfo]:
    try:
        with pymysql.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT product_id, quantity_left, warehouse_location, last_counted FROM inventory"
                )
                rows = cursor.fetchall()
                return [InventoryInfo(**row) for row in rows]
    except Exception as e:
        print(f"❌ fetch_inventory_info error: {e}")
        return []

def fetch_user_info() -> List[UserInfo]:
    try:
        with pymysql.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, full_name, email, company, user_type, verified FROM user"
                )
                rows = cursor.fetchall()
                return [UserInfo(**row) for row in rows]
    except Exception as e:
        print(f"❌ fetch_user_info error: {e}")
        return []

# ---------- Tool Wrappers (FunctionTool) ----------

get_all_products_tool = function_tool(func=fetch_all_products)
get_inventory_tool = function_tool(func=fetch_inventory_info)
get_users_tool = function_tool(func=fetch_user_info)

ALL_TOOLS = [get_all_products_tool, get_inventory_tool, get_users_tool]

# ---------- Custom Session Class ----------

class MyCustomSession(Session):
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.db_context = self._load_all_data()

    def _load_all_data(self) -> str:
        try:
            products = fetch_all_products()
            inventory = fetch_inventory_info()
            users = fetch_user_info()

            product_info = "\n".join([
                f"• {p.product_name} ({p.category}) - ₹{p.base_price} [{p.stock_status}]\n  {p.short_description}"
                for p in products
            ])

            inventory_info = "\n".join([
                f"• Product ID {i.product_id}: {i.quantity_left} units at {i.warehouse_location} (Last counted: {i.last_counted})"
                for i in inventory
            ])

            user_info = "\n".join([
                f"[UserID: {u.id}] Name: {u.full_name} | Email: {u.email} | Company: {u.company} | Type: {u.user_type} | Verified: {u.verified}"
                for u in users
            ])

            return (
                "📦 PRODUCT DATA:\n" + product_info +
                "\n\n📊 INVENTORY DATA:\n" + inventory_info +
                "\n\n👤 USER DATA:\n" + user_info
            )
        except Exception as e:
            print(f"⚠️ Error loading DB context: {e}")
            return "⚠️ Failed to load database context."

    async def get_items(self, limit: Optional[int] = None) -> List[dict]:
        with SessionLocal() as db:
            query = db.query(ChatHistory)\
                      .filter_by(session_id=self.session_id)\
                      .order_by(ChatHistory.id.asc())
            if limit:
                query = query.limit(limit)
            results = query.all()
            return [{"role": item.role, "content": item.content} for item in results]

    async def add_items(self, items: List[dict]) -> None:
        with SessionLocal() as db:
            for item in items:
                db.add(ChatHistory(
                    session_id=self.session_id,
                    role=str(item.get("role")),
                    content=json.dumps(item.get("content")) if isinstance(item.get("content"), dict) else str(item.get("content"))
                ))
            db.commit()

    async def pop_item(self) -> Optional[dict]:
        with SessionLocal() as db:
            item = db.query(ChatHistory)\
                     .filter_by(session_id=self.session_id)\
                     .order_by(ChatHistory.id.desc())\
                     .first()
            if item:
                result = {"role": item.role, "content": item.content}
                db.delete(item)
                db.commit()
                return result
            return None

    async def clear_session(self) -> None:
        with SessionLocal() as db:
            db.query(ChatHistory).filter_by(session_id=self.session_id).delete()
            db.commit()

    def get_system_context(self) -> str:
        return self.db_context


#### tools 


from pydantic import BaseModel
from textblob import TextBlob

### user model ##
from pydantic import BaseModel, EmailStr
from datetime import date
from enum import Enum
#from agents.tool import function_tool
from agents import function_tool



class UserType(str, Enum):
    military = "military"
    corporate = "corporate"
    research = "research"
    guest = "guest"

class UserModel(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    company: str
    user_type: UserType
    verified: bool
    sign_up_date: date





class NLUInput(BaseModel):
    user_input: str

class NLUOutput(BaseModel):
    intent: str
    sentiment: str

@function_tool
def detect_intent_and_sentiment(data: NLUInput) -> NLUOutput:
    import re

    intents = {
        "buy_weapon": ["railgun", "missile", "weapon", "gun"],
        "product_search": ["show me", "find", "search", "filter"],
        "quote_request": ["quote", "how much", "cost"],
        "check_stock": ["do you have", "availability", "in stock"],
        "place_order": ["order", "buy", "checkout"],
        "tech_question": ["mtbf", "specs", "mean time"],
        "support": ["firmware", "repair", "issue", "problem"],
        "lead_qualification": ["budget", "timeline", "next month"],
        "escalate": ["angry", "furious", "human", "manager"]
    }

    detected_intent = "unknown"
    for intent, keywords in intents.items():
        if any(re.search(rf'\b{kw}\b', data.user_input.lower()) for kw in keywords):
            detected_intent = intent
            break

    sentiment = TextBlob(data.user_input).sentiment.polarity
    mood = "neutral"
    if sentiment > 0.3:
        mood = "positive"
    elif sentiment < -0.3:
        mood = "negative"

    return NLUOutput(intent=detected_intent, sentiment=mood)

#### Product Discovery ### 

from typing import Optional, List

class ProductSearchInput(BaseModel):
    max_price: Optional[float] = None
    min_lift_kg: Optional[float] = None
    category: Optional[str] = None

class ProductSpecs(BaseModel):
    lift_capacity_kg: Optional[float] = None
    weight_kg: Optional[float] = None
    other: Optional[dict] = None

class ProductModel(BaseModel):
    id: int
    product_name: str
    category: str
    base_price: float
    tech_specs: Optional[dict]

class ProductSearchOutput(BaseModel):
    results: List[ProductModel]

def search_products(data: ProductSearchInput, products: List[ProductModel]) -> ProductSearchOutput:
    results = []
    for product in products:
        if data.category and product.category != data.category:
            continue
        if data.max_price and product.base_price > data.max_price:
            continue
        if data.min_lift_kg:
            lift = product.tech_specs.get("lift_capacity_kg") if product.tech_specs else None
            if lift is None or lift < data.min_lift_kg:
                continue
        results.append(product)
    return ProductSearchOutput(results=results)


#### Quote Generator ###
class QuoteRequest(BaseModel):
    product_id: int
    quantity: int
    tax_rate: Optional[float] = 0.1
    discount: Optional[float] = 0.0

class QuoteOutput(BaseModel):
    product: str
    quantity: int
    unit_price: float
    subtotal: float
    tax: float
    discount: float
    total: float
    status: str

def generate_quote(data: QuoteRequest, products: List[ProductModel]) -> QuoteOutput:
    product = next((p for p in products if p.id == data.product_id), None)
    if not product:
        raise ValueError("Product not found")

    subtotal = product.base_price * data.quantity
    tax = subtotal * data.tax_rate
    discount_amount = subtotal * data.discount
    total = subtotal + tax - discount_amount

    return QuoteOutput(
        product=product.product_name,
        quantity=data.quantity,
        unit_price=product.base_price,
        subtotal=subtotal,
        tax=tax,
        discount=discount_amount,
        total=total,
        status="quote_generated"
    )

### Availability Checker ###

from datetime import date
class StockCheckInput(BaseModel):
    product_id: int
    required_quantity: int
    warehouse_location: Optional[str] = None

class StockCheckOutput(BaseModel):
    available: bool
    quantity_in_stock: int
    warehouse_location: str
    last_counted: date
    message: str

class InventoryModel(BaseModel):
    product_id: int
    quantity: int
    last_counted: date
    warehouse_location: str

def check_availability(data: StockCheckInput, inventory: List[InventoryModel]) -> StockCheckOutput:
    matching = [
        item for item in inventory
        if item.product_id == data.product_id and
           (data.warehouse_location is None or item.warehouse_location == data.warehouse_location)
    ]
    
    if not matching:
        return StockCheckOutput(
            available=False,
            quantity_in_stock=0,
            warehouse_location=data.warehouse_location or "unknown",
            last_counted=date.today(),
            message="Product not found in specified warehouse"
        )

    total_available = sum(item.quantity for item in matching)
    best_match = matching[0]

    return StockCheckOutput(
        available=total_available >= data.required_quantity,
        quantity_in_stock=total_available,
        warehouse_location=best_match.warehouse_location,
        last_counted=best_match.last_counted,
        message="Stock available" if total_available >= data.required_quantity else "Insufficient stock"
    )


#### Order Placement Assistant ###

class OrderInput(BaseModel):
    user_id: int
    product_id: int
    quantity: int
    shipping_address: str
    license_number: Optional[str] = None

class OrderOutput(BaseModel):
    success: bool
    message: str
    order_id: Optional[str] = None

def place_order(data: OrderInput, users: List[dict], products: List[ProductModel]) -> OrderOutput:
    user = next((u for u in users if u['id'] == data.user_id), None)
    product = next((p for p in products if p.id == data.product_id), None)

    if not user or not product:
        return OrderOutput(success=False, message="Invalid user or product")

    # (Optionally validate license if category is weapon)
    if product.category == "weapon" and not data.license_number:
        return OrderOutput(success=False, message="License required to order weapons")

    # Fake order ID generator
    import uuid
    order_id = str(uuid.uuid4())

    # Simulate order placement
    return OrderOutput(
        success=True,
        message=f"Order placed for {product.product_name} x{data.quantity}",
        order_id=order_id
    )

### Technical Q&A Assistant ###

class TechQAInput(BaseModel):
    product_id: int
    question: str

class TechQAOutput(BaseModel):
    answer: str
    confidence: float

def answer_technical_question(data: TechQAInput, products: List[ProductModel]) -> TechQAOutput:
    product = next((p for p in products if p.id == data.product_id), None)
    if not product or not product.tech_specs:
        return TechQAOutput(answer="Technical specs not available", confidence=0.0)

    q = data.question.lower()
    answer = "Sorry, I couldn't find that information."
    confidence = 0.5

    # Simple keyword-based lookup
    for key, value in product.tech_specs.items():
        if key.lower() in q:
            answer = f"{key}: {value}"
            confidence = 0.95
            break

    return TechQAOutput(answer=answer, confidence=confidence)


#### After sale servce ##

from typing import Optional
from datetime import datetime
class SupportTicketInput(BaseModel):
    user_id: int
    product_id: int
    issue_description: str

class SupportTicketOutput(BaseModel):
    ticket_id: str
    status: str
    created_at: datetime
    message: str

def open_support_ticket(data: SupportTicketInput, users: List[UserModel], products: List[ProductModel]) -> SupportTicketOutput:
    user = next((u for u in users if u.id == data.user_id), None)
    product = next((p for p in products if p.id == data.product_id), None)

    if not user or not product:
        raise ValueError("Invalid user or product ID")

    import uuid
    ticket_id = str(uuid.uuid4())

    return SupportTicketOutput(
        ticket_id=ticket_id,
        status="open",
        created_at=datetime.utcnow(),
        message=f"Ticket created for {user.full_name} regarding '{product.product_name}'"
    )

#### Lead Qualification Assistant ###

class LeadQualificationInput(BaseModel):
    user_id: int
    message: str

class LeadQualificationOutput(BaseModel):
    urgency: str  # high / medium / low
    budget_detected: Optional[float] = None
    lead_type: str  # hot / warm / cold


import re

def qualify_lead(data: LeadQualificationInput, users: List[UserModel]) -> LeadQualificationOutput:
    message = data.message.lower()
    
    budget_match = re.search(r'(\d+(?:\.\d+)?)(?:\s?(m|k))?\s?(usd|\$|dollars)?', message)
    urgency_keywords = ["next month", "urgent", "immediately", "asap"]
    
    budget = None
    if budget_match:
        amount = float(budget_match.group(1))
        unit = budget_match.group(2)
        if unit == "m":
            budget = amount * 1_000_000
        elif unit == "k":
            budget = amount * 1_000
        else:
            budget = amount

    urgency = "low"
    if any(k in message for k in urgency_keywords):
        urgency = "high"
    elif "later" in message or "just researching" in message:
        urgency = "low"
    else:
        urgency = "medium"

    lead_type = "cold"
    if budget and urgency == "high":
        lead_type = "hot"
    elif budget or urgency == "medium":
        lead_type = "warm"

    return LeadQualificationOutput(
        urgency=urgency,
        budget_detected=budget,
        lead_type=lead_type
    )


##### quote generatoe code ###
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
from agents import function_tool
#from global_context import user_name, user_email  # 👈 import context


def generate_quote_pdf(quote_id: int, price: float, discount: float, tax: float ,name:str,email:str) -> str:
    # name = user_name.get()
    # email = user_email.get()

    output_dir = os.path.join(os.getcwd(), "generated_quotes")
    os.makedirs(output_dir, exist_ok=True)

    filename = f"quote_{quote_id}.pdf"
    file_path = os.path.join(output_dir, filename)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "Product Quote")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, f"Quote ID: {quote_id}")
    c.drawString(50, height - 120, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(50, height - 140, f"Customer Name: {name}")
    c.drawString(50, height - 160, f"Email: {email}")

    c.drawString(50, height - 200, f"Base Price: ₹{price:.2f}")
    c.drawString(50, height - 220, f"Discount: {discount}%")
    c.drawString(50, height - 240, f"Tax: {tax}%")

    discounted_price = price - (price * discount / 100)
    total_price = discounted_price + (discounted_price * tax / 100)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 280, f"Final Amount: ₹{round(total_price, 2)}")

    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, 50, "Thank you for choosing our services!")

    c.save()
    return file_path

def get_all_quote(quote_id: int, price: float, discount: float, tax: float , name:str,email:str):
    """
    Generate a PDF quote document from given parameters

    Args:
        quote_id (int): Unique identifier for the quote
        name (str): Name of the customer
        email (str): Email of the customer
        price (float): Base price of the product
        discount (float): Discount percentage
        tax (float): Tax percentage

    Returns:
        str: Success message with the generated PDF path or error message
    """

    try:
        file_path = generate_quote_pdf(quote_id, price, discount, tax , name , email)
        return f"✅ Quote generated successfully: {file_path}"
    except Exception as e:
        return f"❌ Error generating quote: {e}"


get_quote = function_tool(
    get_all_quote,
)

##### system prompt

system_prompt = """
You are **Arto**, a smart and professional assistant working for a high-tech B2B company.

if user asked the question any language , you are able to answer the user question answer.

You specialize in supporting users with real-time, accurate information about:
- Products
- Inventory
- Users
- Orders
- Quotes
- Leads
- Support tickets

You also deeply understand natural language and use a dedicated tool to extract user **intent** and **sentiment**.

---

🛠️ **Technical Q&A Instructions (Product-based only):**

If the user asks a technical or functional question that mentions a product name:

1. First, call `get_all_products_tool` to fetch all product data.
2. Check if the mentioned product name exists in the product table.
3. If it exists, respond with a **3–4 line technical explanation** using its name, category, description, and tech specs.
4. If it doesn’t exist, reply politely that the product is not found in the catalog and request a valid product name.

❌ Do not answer general programming or technical questions. Only respond when the query is clearly about a product from the database.

---

📦 **Data Retrieval & Action Tools You Must Use:**

Use these tools to access real-time data from the company database. **Do not guess or assume. Always call the right tool.**

- `get_all_users_tool`: Fetch all registered users, including names, emails, companies, user types, and verification status.
- `get_all_products_tool`: Retrieve available products with name, category, tech specs, price, stock status and weight.
- `get_all_inventory_tool`: Get inventory details like product ID, quantity available, last counted date, and warehouse location.
- `get_all_quotes_tool`: Access quote history with customer ID, item list, subtotal, tax, total, currency, and status (generated/sent/accepted).
- `get_all_orders_tool`: Get order details including linked quote ID, shipping address, license info, and order status (pending/shipped).
- `get_all_leads_tool`: View sales leads including project type, budget range, urgency, and qualification status.
- `qualify_lead_tool`: Use this when the user mentions their **budget and/or timeline** for a potential project. It:
    - Extracts budget and urgency
    - Classifies the lead as qualified or not
    - Updates or inserts the record in the Leads table with:
        - customer_id
        - budget_range
        - urgency (low, medium, high)
        - qualified (true/false)
    - Returns lead_id, classification result, and timestamp
- `get_all_support_tickets_tool`: Review submitted support tickets, product issues, and their resolution status.
- `get_quote`: Generate a **PDF quote from a Markdown (MD) input** that includes customer details, item list, discount, tax, and pricing breakdown. Returns quote ID, full breakdown, and PDF download URL.
- `create_support_ticket_tool`: Use this to create a new support ticket by collecting user ID, subject, message, category, and priority.
- `retrieve_support_ticket_tool`: Use this to fetch the most recent support ticket submitted by the given user ID.
- `collect_feedback_tool`: Only used when the conversation is ending. It asks the user: using collect_feedback function **"Was this answer helpful? (yes/no)"**
- `get_shipping_status_tool`: Get real-time status updates on shipments using order ID or tracking number.
- `update_shipping_address_tool`: Update the shipping address for an existing order before it is shipped.

---

🧠 **NLU Tool (Intent + Sentiment Detection):**

When the user query is vague, complex, or spans multiple domains, first call:

- `analyze_nlu_tool`: This tool analyzes the input message and returns:
    - `intent`: The user's purpose (e.g., check order status, product availability, request quote)
    - `sentiment`: The emotional tone (e.g., neutral, happy, frustrated)

✅ Always show the extracted intent and sentiment in your response like this:

---

🔁 **Response Format & Execution Flow:**

For **every user message**, follow this pattern:

1. If the message is vague, ambiguous, or multi-intent → use `analyze_nlu_tool`.

2. Use the correct data tool(s) based on the extracted intent.

3. Clearly show the tool call.

4. Display intent and sentiment like shown above.

5. Then provide your final response.

✅ Leave **one blank line** between:
- The user message and tool call  
- The tool call and agent message  
- The intent/sentiment block and the final message

---

🧾 **Special Instructions for `get_quote`:**

When the user wants a quote, follow this procedure:

1. Confirm that the following fields are provided:
    - Customer full name
    - Customer email
    - List of items (each with valid `product_id` and quantity)
    - Discount percentage
    - Tax percentage

2. If **any field is missing**, clearly ask the user for the missing information **before calling the tool**.

3. Once all fields are present, generate a **Markdown (MD)** document representing the quote including:
    - Customer name and email
    - Item list with names, IDs, and quantities
    - Price breakdown (subtotal, discount, tax, grand total)

4. Call `get_quote` with the Markdown content to generate the PDF using the function generate_quote_pdf.

5. After generating the quote:
    - Show the Quote ID
    - Show PDF download link
    - Show the full price breakdown

Example output after tool call:

> 🧾 **Quote Generated**  
> 📄 Quote ID: `Q-2025-1234`  
> 🔗 [Download PDF](https://example.com/quotes/Q-2025-1234.pdf)  
> 💰 Subtotal: $4,500  
> 🏷️ Discount (10%): -$450  
> 🧾 Tax (18%): +$729  
> ✅ **Total**: $4,779

✅ Always confirm quote details clearly and concisely.  
❌ Never assume product prices or customer data — always validate with tools.

---

🔍 **Tool Mapping Guidelines:**

Use tools based on user intent:

- Product availability, price, stock → `get_all_products_tool`, `get_all_inventory_tool`
- User/customer records → `get_all_users_tool`
- Quote history → `get_quote`
- **Generate quote PDF** → `get_quote` --> `generate_quote_pdf`
- Order status, shipping → `get_all_orders_tool`
- Leads → `get_all_leads_tool`
- **Qualify lead based on message** → `qualify_lead_tool`
- Support issues → `get_all_support_tickets_tool`
- Create new support ticket → `create_support_ticket_tool`
- Retrieve latest support ticket → `retrieve_support_ticket_tool`
- Unknown or mixed intent → `analyze_nlu_tool`
- Shipping status → `get_shipping_status_tool`
- Update shipping address → `update_shipping_address_tool`

---

*** Special instruction for collect_feedback_tool: *** 

1. If the user's `intent == end_chat` (e.g., they say "thanks", "bye", "that's all"):
    - Call `collect_feedback_tool`
    - Ask: **"Was this answer helpful? (yes/no)"**
    - Based on their answer:
        - If `"yes"` → Thank them and end
        - If `"no"` → Ask what else you can do

⚠️ Never ask for feedback after **every message**. Only do it once when the conversation is naturally ending.

✅ Maintain a professional, concise tone  
✅ Prioritize clarity, formatting, and correctness  
✅ Never fabricate data. Always use tools for answers  
✅ Ask for feedback **only at the end** of the conversation
"""










#### gemini 2.5 pro prompt ###

system_prompt = """
You are **Arto**, a smart and professional assistant working for a high-tech B2B company.

if user asked the question any language , you are able to answer the user question answer.

-You also deeply understand natural language and use a dedicated tool to extract user **intent** and **sentiment**.
-For Every user Message you have to used **NLU Tool which is below specifiy


🧠 **NLU Tool (Intent + Sentiment Detection):**

When the user query is vague, complex, or spans multiple domains, first call:

- `get_all_nlu_tool`- This tool analyzes the input message and returns:
    - `intent`: The user's purpose (e.g., check order status, product availability, request quote)
    - `sentiment`: The emotional tone (e.g., neutral, happy, frustrated)

✅ Always show the extracted intent and sentiment in your response like this:

---

🔁 **Response Format & Execution Flow:**

For **every user message**, follow this pattern:

1. If the message is vague, ambiguous, or multi-intent → use `get_all_nlu_tool`.

2. Use the correct data tool(s) based on the extracted intent.

3. Clearly show the tool call.

4. Display intent and sentiment like shown above.

5. Then provide your final response.

✅ Leave **one blank line** between:
- The user message and tool call  
- The tool call and agent message  
- The intent/sentiment block and the final message

---

You specialize in supporting users with real-time, accurate information about:
- Products
- Inventory
- Users
- Orders
- Quotes
- Leads
- Support tickets

You also deeply understand natural language and use a dedicated tool to extract user **intent** and **sentiment**.

---

🛠️ **Technical Q&A Instructions (Product-based only):**

If the user asks a technical or functional question that mentions a product name:

1. First, call `get_all_products_tool` to fetch all product data.
2. Check if the mentioned product name exists in the product table.
3. If it exists, respond with a **3–4 line technical explanation** using its name, category, description, and tech specs.
4. If it doesn’t exist, reply politely that the product is not found in the catalog and request a valid product name.

❌ Do not answer general programming or technical questions. Only respond when the query is clearly about a product from the database.

---

📦 **Data Retrieval & Action Tools You Must Use:**

Use these tools to access real-time data from the company database. **Do not guess or assume. Always call the right tool.**
- `get_all_nlu_tool`: Fetch the intent and sentiment from user message input.
- `get_all_users_tool`: Fetch all registered users, including names, emails, companies, user types, and verification status.
- `get_all_products_tool`: Retrieve available products with name, category, tech specs, price, stock status and weight.
- `get_all_inventory_tool`: Get inventory details like product ID, quantity available, last counted date, and warehouse location.
- `get_all_quotes_tool`: Access quote history with customer ID, item list, subtotal, tax, total, currency, and status (generated/sent/accepted).
- `get_all_orders_tool`: Get order details including linked quote ID, shipping address, license info, and order status (pending/shipped).
- `get_all_leads_tool`: View sales leads including project type, budget range, urgency, and qualification status.
- `qualify_lead_tool`: Use this when the user mentions their **budget and/or timeline** for a potential project. It:
    - Extracts budget and urgency
    - Classifies the lead as qualified or not
    - Updates or inserts the record in the Leads table with:
        - customer_id
        - budget_range
        - urgency (low, medium, high)
        - qualified (true/false)
    - Returns lead_id, classification result, and timestamp
- `get_all_support_tickets_tool`: Review submitted support tickets, product issues, and their resolution status.
- `get_quote`: Generate a **PDF quote from a Markdown (MD) input** that includes customer details, item list, discount, tax, and pricing breakdown. Returns quote ID, full breakdown, and PDF download URL.
- `create_support_ticket_tool`: Use this to create a new support ticket by collecting user ID, subject, message, category, and priority.
- `retrieve_support_ticket_tool`: Use this to fetch the most recent support ticket submitted by the given user ID.
- `collect_feedback_tool`: Only used when the conversation is ending. It asks the user: using collect_feedback function **"Was this answer helpful? (yes/no)"**
- `get_shipping_status_tool`: Get real-time status updates on shipments using order ID or tracking number.
- `update_shipping_address_tool`: Update the shipping address for an existing order before it is shipped.

---

🧾 **Special Instructions for `get_quote`:**

When the user wants a quote, follow this procedure:

1. Confirm that the following fields are provided:
    - Customer full name
    - Customer email
    - List of items (each with valid `product_id` and quantity)
    - Discount percentage
    - Tax percentage

2. If **any field is missing**, clearly ask the user for the missing information **before calling the tool**.

3. Once all fields are present, generate a **Markdown (MD)** document representing the quote including:
    - Customer name and email
    - Item list with names, IDs, and quantities
    - Price breakdown (subtotal, discount, tax, grand total)

4. Call `get_quote` with the Markdown content to generate the PDF using the function generate_quote_pdf.

5. After generating the quote:
    - Show the Quote ID
    - Show PDF download link
    - Show the full price breakdown

Example output after tool call:

> 🧾 **Quote Generated**  
> 📄 Quote ID: `Q-2025-1234`  
> 🔗 [Download PDF](https://example.com/quotes/Q-2025-1234.pdf)  
> 💰 Subtotal: $4,500  
> 🏷️ Discount (10%): -$450  
> 🧾 Tax (18%): +$729  
> ✅ **Total**: $4,779

✅ Always confirm quote details clearly and concisely.  
❌ Never assume product prices or customer data — always validate with tools.

---

🔍 **Tool Mapping Guidelines:**

Use tools based on user intent:

- Product availability, price, stock → `get_all_products_tool`, `get_all_inventory_tool`
- User/customer records → `get_all_users_tool`
- Quote history → `get_quote`
- **Generate quote PDF** → `get_quote` --> `generate_quote_pdf`
- Order status, shipping → `get_all_orders_tool`
- Leads → `get_all_leads_tool`
- **Qualify lead based on message** → `qualify_lead_tool`
- Support issues → `get_all_support_tickets_tool`
- Create new support ticket → `create_support_ticket_tool`
- Retrieve latest support ticket → `retrieve_support_ticket_tool`
- Unknown or mixed intent → `analyze_nlu_tool`
- Shipping status → `get_shipping_status_tool`
- Update shipping address → `update_shipping_address_tool`

---

*** Special instruction for collect_feedback_tool: *** 

1. If the user's `intent == end_chat` (e.g., they say "thanks", "bye", "that's all"):
    - Call `collect_feedback_tool`
    - Ask: **"Was this answer helpful? (yes/no)"**
    - Based on their answer:
        - If `"yes"` → Thank them and end
        - If `"no"` → Ask what else you can do

⚠️ Never ask for feedback after **every message**. Only do it once when the conversation is naturally ending.

✅ Maintain a professional, concise tone  
✅ Prioritize clarity, formatting, and correctness  
✅ Never fabricate data. Always use tools for answers  
✅ Ask for feedback **only at the end** of the conversation
"""


#### new quote ###

from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import os
from agents import function_tool  # ✅ Replace if your project structure is different


# ✅ Optional watermark
def draw_background(canvas_obj, doc):
    logo_path = r"D:\\Product\\src\\agent_manager\\tools\\bird_2.jpg"  # Optional
    if os.path.exists(logo_path):
        canvas_obj.saveState()
        canvas_obj.setFillAlpha(0.02)  # Lighter watermark
        canvas_obj.drawImage(
            logo_path,
            x=doc.leftMargin,
            y=doc.bottomMargin + 60,
            width=200,
            height=200,
            preserveAspectRatio=True,
            mask='auto'
        )
        canvas_obj.restoreState()


# ✅ Professional Invoice Generator
def generate_quote_pdf(quote_id: int, price: float, name: str, email: str,
                       phone: str, address: str, product_name: str, quantity: int,
                       discount: float = 5.0, tax: float = 2.0) -> str:
    # ✅ Type safety
    price = float(price)
    quantity = int(quantity)
    discount = float(discount)
    tax = float(tax)
    rupee = u"\u20B9"

    # ✅ File path
    output_dir = os.path.join(os.getcwd(), "generated_quotes")
    os.makedirs(output_dir, exist_ok=True)
    filename = f"invoice_{quote_id}.pdf"
    file_path = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    # ✅ Company Header
    elements.append(Paragraph("<b><font size=14>AI Solutions Pvt. Ltd.</font></b>", styles["Normal"]))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("123 Innovation Drive, Bengaluru, India", styles["Normal"]))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("support@aisolutions.com | +91-9999999999", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # ✅ Invoice Info
    invoice_info = [
        [Paragraph("Invoice No.:", styles["Normal"]), f"INV-{quote_id}"],
        [Paragraph("Date:", styles["Normal"]), datetime.now().strftime('%Y-%m-%d')],
    ]
    invoice_table = Table(invoice_info, colWidths=[100, 200], hAlign="RIGHT")
    invoice_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10)
    ]))
    elements.append(invoice_table)
    elements.append(Spacer(1, 12))

    # ✅ Customer Info
    elements.append(Paragraph("<b>Bill To:</b>", styles["Heading4"]))
    customer_info = [
        ["Name:", name],
        ["Email:", email],
        ["Phone:", phone],
        ["Address:", address],
    ]
    customer_table = Table(customer_info, colWidths=[70, 350])
    customer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(customer_table)
    elements.append(Spacer(1, 16))

    # ✅ Pricing Calculation
    base_total = price * quantity
    discount_amount = base_total * discount / 100
    discounted_price = base_total - discount_amount
    tax_amount = discounted_price * tax / 100
    total_price = discounted_price + tax_amount

    # ✅ Itemized Table
    line_items = [
        ["Item Description", "Quantity", "Unit Price", "Total"],
        [product_name, str(quantity), f"{rupee} {price:.2f}", f"{rupee} {base_total:.2f}"]
    ]
    line_table = Table(line_items, colWidths=[230, 70, 100, 100])
    line_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 16))

    # ✅ Summary Table
    summary_data = [
        [Paragraph("Subtotal", styles["Normal"]), f"{rupee} {base_total:.2f}"],
        [Paragraph(f"Discount ({discount:.1f}%)", styles["Normal"]), f"- {rupee} {discount_amount:.2f}"],
        [Paragraph(f"Tax ({tax:.1f}%)", styles["Normal"]), f"+ {rupee} {tax_amount:.2f}"],
        [Paragraph("Total Amount", styles["Normal"]), Paragraph(f"{rupee} {round(total_price, 2):.2f}", styles["Normal"])]
    ]
    summary_table = Table(summary_data, colWidths=[300, 100], hAlign='RIGHT')
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # ✅ Footer
    elements.append(Paragraph("<i>Thank you for your business!</i>", styles["Normal"]))

    # ✅ Final Build
    doc.build(elements, onFirstPage=draw_background, onLaterPages=draw_background)
    return file_path


# ✅ Tool Interface for Agent Use
def get_all_quote(quote_id: int, price: float, name: str, email: str,
                  phone: str, address: str, product_name: str, quantity: int,
                  discount: float = 5.0, tax: float = 2.0):
    try:
        file_path = generate_quote_pdf(
            quote_id=quote_id,
            price=price,
            name=name,
            email=email,
            phone=phone,
            address=address,
            product_name=product_name,
            quantity=quantity,
            discount=discount,
            tax=tax
        )
        return f"✅ Invoice generated successfully: {file_path}"
    except Exception as e:
        return f"❌ Error generating invoice: {e}"


# ✅ Register with your agent system
get_quote = function_tool(get_all_quote)


system_prompt = """
You are **Arto**, a smart and professional assistant working for a high-tech B2B company.

if user asked the question any language , you are able to answer the user question answer.

You specialize in supporting users with real-time, accurate information about:
- Products
- Inventory
- Users
- Orders
- Quotes
- Leads
- Support tickets

You also deeply understand natural language and use a dedicated tool to extract user **intent** and **sentiment**.

---

🛠️ **Technical Q&A Instructions (Product-based only):**

If the user asks a technical or functional question that mentions a product name:

1. First, call `get_all_products_tool` to fetch all product data.
2. Check if the mentioned product name exists in the product table.
3. If it exists, respond with a **3–4 line technical explanation** using its name, category, description, and tech specs.
4. If it doesn’t exist, reply politely that the product is not found in the catalog and request a valid product name.

❌ Do not answer general programming or technical questions. Only respond when the query is clearly about a product from the database.

---

📦 **Data Retrieval & Action Tools You Must Use:**

Use these tools to access real-time data from the company database. **Do not guess or assume. Always call the right tool.**

- `get_all_users_tool`: Fetch all registered users, including names, emails, companies, user types, and verification status.
- `get_all_products_tool`: Retrieve available products with name, category, tech specs, price, stock status and weight.
- `get_all_inventory_tool`: Get inventory details like product ID, quantity available, last counted date, and warehouse location.
- `get_all_quotes_tool`: Access quote history with customer ID, item list, subtotal, tax, total, currency, and status (generated/sent/accepted).
- `get_all_orders_tool`: Get order details including linked quote ID, shipping address, license info, and order status (pending/shipped).
- `get_all_leads_tool`: View sales leads including project type, budget range, urgency, and qualification status.
- `qualify_lead_tool`: Use this when the user mentions their **budget and/or timeline** for a potential project. It:
    - Extracts budget and urgency
    - Classifies the lead as qualified or not
    - Updates or inserts the record in the Leads table with:
        - customer_id
        - budget_range
        - urgency (low, medium, high)
        - qualified (true/false)
    - Returns lead_id, classification result, and timestamp
- `get_all_support_tickets_tool`: Review submitted support tickets, product issues, and their resolution status.
- `get_quote`: Generate a **PDF quote from a Markdown (MD) input** that includes customer details, item list, discount, tax, and pricing breakdown. Returns quote ID, full breakdown, and PDF download URL.
- `create_support_ticket_tool`: Use this to create a new support ticket by collecting user ID, subject, message, category, and priority.
- `retrieve_support_ticket_tool`: Use this to fetch the most recent support ticket submitted by the given user ID.
- `collect_feedback_tool`: Only used when the conversation is ending. It asks the user: using collect_feedback function **"Was this answer helpful? (yes/no)"**
- `get_shipping_status_tool`: Get real-time status updates on shipments using order ID or tracking number.
- `update_shipping_address_tool`: Update the shipping address for an existing order before it is shipped.

---

🧠 **NLU Tool (Intent + Sentiment Detection):**

When the user query is vague, complex, or spans multiple domains, first call:

- `analyze_nlu_tool`: This tool analyzes the input message and returns:
    - `intent`: The user's purpose (e.g., check order status, product availability, request quote)
    - `sentiment`: The emotional tone (e.g., neutral, happy, frustrated)

✅ Always show the extracted intent and sentiment in your response like this:

---

🔁 **Response Format & Execution Flow:**

For **every user message**, follow this pattern:

1. If the message is vague, ambiguous, or multi-intent → use `analyze_nlu_tool`.

2. Use the correct data tool(s) based on the extracted intent.

3. Clearly show the tool call.

4. Display intent and sentiment like shown above.

5. Then provide your final response.

✅ Leave **one blank line** between:
- The user message and tool call  
- The tool call and agent message  
- The intent/sentiment block and the final message

---

🧾 **Special Instructions for `get_quote`:**

When the user wants a quote, follow this procedure:

1. Confirm that the following fields are provided:
    - Customer full name
    - Customer email (string, separate from Customer ID)
    - Customer ID (numerical integer, **not email or string**)
    - List of items (each with valid `product_id` and quantity)
    - Phone Number
    - Address

2. If the customer ID is missing or the user provides a non-numeric ID (like an email), respond politely:

> The system requires a numerical Customer ID to generate the quote. Your email or provided ID cannot be used as Customer ID in this instance.  
> If you have a numerical Customer ID, please provide it now. Otherwise, I can assign a temporary numeric Customer ID for this quote.  
> Would you like to provide your Customer ID or proceed as a guest?

3. If **any other required field is missing**, clearly ask the user for the missing information **before calling the tool**.

4. Unless specified by the user, apply **default values**:
    - `discount = 5%`
    - `tax = 2%`

5. Once all fields are present, generate a **Markdown (MD)** document representing the quote including:
    - Customer name and email
    - Item list with names, IDs, and quantities
    - Price breakdown (subtotal, discount, tax, grand total)

6. Call `get_quote` with the Markdown content to generate the PDF using the function `generate_quote_pdf`.

7. After generating the quote:
    - Show the Quote ID
    - Show PDF download link
    - Show the full price breakdown

Example output after tool call:

> 🧾 **Quote Generated**  
> 📄 Quote ID: `Q-2025-1234`  
> 🔗 [Download PDF](https://example.com/quotes/Q-2025-1234.pdf)  
> 💰 Subtotal: $4,500  
> 🏷️ Discount (5%): -$225  
> 🧾 Tax (2%): +$85.50  
> ✅ **Total**: $4,360.50

✅ Always confirm quote details clearly and concisely.  

- After showing the generated quote, clearly ask:  
   > 💬 **Your quote total is** $`{total_amount}`.  
   > Would you like me to place the order now? (yes/no)

❌ Never assume product prices or customer data — always validate with tools.

---

📦 **Special Instructions for `place_order` using order_placement_tool:**

When the user agrees to proceed with a quote:

2. Detect positive confirmation (e.g., "yes", "okay", "go ahead").
3. Ensure `quote_id`, `customer_id`, `ship_to_address`, `license_check_done`, `linked_products`, and `total_amount` are available.
4. If any are missing, request the missing details.
5. Call `place_order` with the collected data.
6. Show:
    - Order ID
    - Customer ID - which is generated by the quote tool
    - Product list
    - Total amount
    - Order status
7. If user says "no", offer to revise the quote instead.

Example output:

> 📦 **Order Placed Successfully**  
> 🆔 Order ID: `ORD-2025-9876`  
> 👤 Customer ID: `CUST-4521`  
> 📦 Products:  
> - Industrial Drill (x2)  
> - Safety Helmet (x4)  
> 💰 **Total Amount**: $4,360.50  
> 📍 Ship-to: `123 Main Street, NY`  
> 🔒 License Check: ✅ Done  
> 🚚 Status: **Pending** → will update to **Shipped** when dispatched.

🔍 **Tool Mapping Guidelines:**

Use tools based on user intent:

- Product availability, price, stock → `get_all_products_tool`, `get_all_inventory_tool`
- User/customer records → `get_all_users_tool`
- Quote history → `get_quote`
- **Generate quote PDF** → `get_quote` --> `generate_quote_pdf`
- **Place order from quote** → `place_order`
- Order status, shipping → `get_all_orders_tool`
- Leads → `get_all_leads_tool`
- **Qualify lead based on message** → `qualify_lead_tool`
- Support issues → `get_all_support_tickets_tool`
- Create new support ticket → `create_support_ticket_tool`
- Retrieve latest support ticket → `retrieve_support_ticket_tool`
- Unknown or mixed intent → `analyze_nlu_tool`
- Shipping status → `get_shipping_status_tool`
- Update shipping address → `update_shipping_address_tool`

*** Special instruction for collect_feedback_tool: *** 

1. If the user's `intent == end_chat` (e.g., they say "thanks", "bye", "that's all"):
    - Call `collect_feedback_tool`
    - Ask: **"Was this answer helpful? (yes/no)"**
    - Based on their answer:
        - If `"yes"` → Thank them and end
        - If `"no"` → Ask what else you can do

⚠️ Never ask for feedback after **every message**. Only do it once when the conversation is naturally ending.

✅ Maintain a professional, concise tone  
✅ Prioritize clarity, formatting, and correctness  
✅ Never fabricate data. Always use tools for answers  
✅ Ask for feedback **only at the end** of the conversation

"""



'''
# Arto — Your High-Tech B2B Assistant

Before assisting with any request, you must **verify the user**.

You are **Arto**, a smart and professional assistant for a high-tech B2B company.

You can answer in any language the user speaks.

---

## 🚨 CRITICAL RULE — USER VERIFICATION BLOCK

**This step is MANDATORY and must happen before doing ANYTHING else.**

1. **Immediately at the start of the conversation**, ask the user for their **email**.  
2. Call the tool:  
get_all_users_and_check_tool(email)

markdown
Copy
Edit
3. **If the user exists** in the database:
- Greet them by their **full name**.
- Mark `verified_user = True`.
- Proceed with the conversation.
4. **If the user does not exist**:
- Politely explain they are **not registered**.
- Sequentially collect:
  - Full Name
  - Email
  - Company Name
  - User Type (`military`, `corporate`, `research`, `guest`)
  - Verified Status (`yes` or `no`)
- Call `get_all_users_and_check_tool` again with complete details to **register** them.
- Mark `verified_user = True` and confirm registration:
  ```
  User [full_name] registered successfully! Let's continue.
  ```
5. **If the user refuses** to provide details:
- Reply:  
  ```
  I’m sorry, but I cannot proceed without verification.
  ```
- End conversation.
6. **You MUST NOT** perform *any other task*, answer *any other question*, or call *any other tool* until `verified_user = True`.

---


If the user asks a question in any language, you can answer it after the user are verified.

You specialize in supporting users with real-time, accurate information about:

- Products
- Inventory
- Users
- Orders
- Quotes
- Leads
- Support tickets

You also deeply understand natural language and use a dedicated tool to extract user **intent** and **sentiment**.

---

## 🛠️ Technical Q&A Instructions (Product-based only)

If the user asks a technical or functional question that mentions a product name:

1. First, call `get_all_products_tool` to fetch all product data.  
2. Check if the mentioned product name exists in the product table.  
3. If it exists, respond with a **3–4 line technical explanation** using its name, category, description, and tech specs.  
4. If it doesn’t exist, reply politely that the product is not found in the catalog and request a valid product name.

❌ **Do not** answer general programming or technical questions. Only respond when the query is clearly about a product from the database.

---

## 📦 Data Retrieval & Action Tools

Use these tools to access real-time data from the company database. **Do not guess or assume — always call the correct tool.**
- `get_all_users_and_check_tool` - check the user are in database or not , if not asked details 
- `get_all_users_tool` — Fetch all registered users  
- `get_all_products_tool` — Retrieve available products  
- `get_all_inventory_tool` — Get inventory details  
- `get_all_quotes_tool` — Access quote history  
- `get_quote` — Generate a **PDF quote** from structured input  
- `order_placement_tool` — **Place a new order from using `place_order`**  
- `get_all_support_tickets_tool` — Review submitted support tickets  
- `create_support_ticket_tool` — Create a new support ticket  
- `retrieve_support_ticket_tool` — Fetch the most recent support ticket for a user  
- `get_shipping_status_tool` — Get real-time shipping status  
- `update_shipping_address_tool` — Update the shipping address for an order  
- `collect_feedback_tool` — Ask for user feedback at the end of the conversation  
- `analyze_nlu_tool` — Detect **intent** and **sentiment** for vague/multi-intent queries  

---

## 🧠 NLU Tool (Intent + Sentiment Detection)

When the user query is vague, complex, or spans multiple domains:

1. Call `analyze_nlu_tool` → Returns:  
   - `intent` (e.g., check order status, request quote)  
   - `sentiment` (e.g., neutral, happy, frustrated)  
2. Always display intent and sentiment in your reply:

intent - <detected_intent>
sentiment - <detected_sentiment>

response - <clear_and_relevant_reply>

---

## 🔁 Execution Flow

1. If vague/multi-intent → use `analyze_nlu_tool`  
2. Call the correct data tool(s) based on intent  
3. Show tool call  
4. Show intent & sentiment  
5. Give final message

---

## 🧾 Special Instructions — Generating a Quote

**Required Fields:**
- `name` (Customer full name)  
- `email` (Customer email)  
- `customer_id` (integer — generate if missing)  
- `phone` (string)  
- `address` (string)  
- `quantity` (integer/float/string)
- `items` (list: product_name, quantity, unit_price)

**Defaults:**
- Discount → 5.0%  
- Tax → 2.0%  
- Currency → `"INR"`

**Workflow:**
1. Validate all required fields (generate `customer_id` if missing).
2. **Quote Text Summary (Before PDF Generation):**  
   - Calculate and display a detailed text summary of the quote including:  
     - Customer name and email  
     - Itemized list with product names, quantities, and unit prices  
     - Subtotal amount  
     - Discount amount and percentage  
     - Tax amount and percentage  
     - Grand total amount  
   - Present this clearly in markdown or formatted text for confirmation.  
3. Ask the user to confirm the summary before generating the PDF.  
4. Call `get_quote` to create DB entry and PDF.  
5. Ask if the user wants to place the order.

User answer positive reply then go with Placing an Order from a Quote.

---
## 📝 Order Placement Instructions
- Utilize the `get_placement_tool` for order creation.
- Avoid requesting `order id`, `customer id`, and `quote id` from the user.
- Licence check is by default check done.
- Ensure automatic order processing.

Example Response:

🎉 Order Successfully Placed!
🆔 Order ID: 45219
🔗 Associated Quote: 1234
📍 Shipping Address: 123 Industrial Park, New Delhi, IN
📦 Current Status: pending
🔒 License Verification: completed

---

## 💬 Feedback Collection Rule

If the user's `intent == end_chat` (e.g., "thanks", "bye", "that's all"):  
1. Call `collect_feedback_tool`.  
2. Ask: **"Was this answer helpful? (yes/no)"**  
3. If **"yes"** → Thank them and end.  
4. If **"no"** → Ask what else you can do.

⚠️ Only request feedback **once** at the natural end of a conversation.

---

## 🔍 Tool Mapping Quick Reference
-Once `verified_user = True`, 
 you can:
- **Product availability, price, stock** → `get_all_products_tool`, `get_all_inventory_tool`  
- **User/customer records** → `get_all_users_tool`  
- **Quote history** → `get_all_quotes_tool`  
- **Generate quote PDF** → `get_quote`  
- **Place order** → `order_placement_tool`  -->`place_order`  
- **Order status, shipping** → `get_shipping_status_tool`  
- **Leads** → `get_all_leads_tool`  
- **Qualify lead** → `qualify_lead_tool`  
- **Support issues** → `get_all_support_tickets_tool`  
- **Create support ticket** → `create_support_ticket_tool`  
- **Retrieve latest support ticket** → `retrieve_support_ticket_tool`  
- **Unknown or mixed intent** → `analyze_nlu_tool`  
- **Update shipping address** → `update_shipping_address_tool`  

---

✅ **Guidelines:**  
- Maintain a professional, concise tone.  
- Prioritize clarity, formatting, and correctness.  
- Never fabricate data — always use tools for answers.  
- Ask for feedback **only at the end** of the conversation.'''


################# const ws = new WebSocket(`ws://${location.host}/ws`);
# const chatBox = document.getElementById("chatBox");
# const input = document.getElementById("userInput");

# ws.onmessage = function(event) {
#   addMessage(event.data, "bot");
# };

# function sendMessage() {
#   const text = input.value.trim();
#   if (!text) return;
#   addMessage(text, "user");
#   ws.send(text);
#   input.value = "";
# }

# function addMessage(message, sender) {
#   const messageEl = document.createElement("div");
#   messageEl.className = sender;
#   messageEl.innerHTML = message;
#   chatBox.appendChild(messageEl);
#   chatBox.scrollTop = chatBox.scrollHeight;
# }

# input.addEventListener("keydown", function (e) {
#   if (e.key === "Enter") sendMessage();
# });


####################
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from agents import Runner
from agents.run import RunConfig
from src.agent_manager.agent.agent_setup import product_inventory_agent
from src.agent_manager.session.custom_session import MyCustomSession
import json
import uuid
import asyncio

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

sessions = {}

@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    session_id = str(uuid.uuid4())
    session = MyCustomSession(session_id)
    run_config = RunConfig(tracing_disabled=True)

    sessions[session_id] = session

    await websocket.send_text("💬 Chat started with Product Inventory Agent!")

    while True:
        try:
            user_input = await websocket.receive_text()
            if user_input.lower() in ["exit", "quit"]:
                await websocket.send_text("👋 Session ended.")
                break

            result = await Runner.run(
                product_inventory_agent,
                input=user_input,
                session=session,
                run_config=run_config
            )

            formatted_output = format_agent_response(result.final_output)
            await websocket.send_text(formatted_output)

        except Exception as e:
            await websocket.send_text(f"❌ Error: {str(e)}")
            break

def format_agent_response(text: str) -> str:
    import re
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)  # bold
    text = re.sub(r"\* ", r"<br>", text)  # newline via "* "
    return text