import uuid
import os
from datetime import datetime
import enum

from sqlalchemy import (
    Column, Integer, String, Float, Enum, create_engine
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph

from agents import function_tool  # Adjust import based on your project
from src.model.model import Quote , QuoteStatus
from src.db.db import  SessionLocal



# Base = declarative_base()

# # Change your DB connection string here
# DATABASE_URL = "mysql+pymysql://username:password@localhost/b2b"
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(bind=engine)
# Base.metadata.create_all(bind=engine)


def draw_background(canvas_obj, doc):
    logo_path = r"D:\\Product\\src\\agent_manager\\tools\\bird_2.jpg"
    if os.path.exists(logo_path):
        canvas_obj.saveState()
        canvas_obj.setFillAlpha(0.02)
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

def generate_quote_pdf(customer_id, quote_id, items, discount=5.0, tax=2.0, currency="INR"):
    if not customer_id:
        customer_id = str(uuid.uuid4())[:8]

    base_total = sum(item['quantity'] * item['unit_price'] for item in items)
    discount_amount = base_total * discount / 100
    discounted_price = base_total - discount_amount
    tax_amount = discounted_price * tax / 100
    total_price = discounted_price + tax_amount

    rupee = u"\u20B9" if currency == "INR" else currency

    output_dir = os.path.join(os.getcwd(), "generated_quotes")
    os.makedirs(output_dir, exist_ok=True)
    filename = f"invoice_{customer_id}_{quote_id}.pdf"
    file_path = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b><font size=14>AI Solutions Pvt. Ltd.</font></b>", styles["Normal"]))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("123 Innovation Drive, Bengaluru, India", styles["Normal"]))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("support@aisolutions.com | +91-9999999999", styles["Normal"]))
    elements.append(Spacer(1, 12))

    invoice_info = [
        ["Invoice No.", ":", f"INV-{quote_id}"],
        ["Customer ID", ":", customer_id],
        ["Date", ":", datetime.now().strftime('%Y-%m-%d')],
    ]
    invoice_table = Table(invoice_info, colWidths=[80, 10, 150], hAlign="RIGHT")
    invoice_table.setStyle(TableStyle([
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10)
    ]))
    elements.append(invoice_table)
    elements.append(Spacer(1, 12))

    line_items = [["Item Description", "Quantity", "Unit Price", "Total"]]
    for item in items:
        total = item['quantity'] * item['unit_price']
        line_items.append([
            item['product_name'],
            str(item['quantity']),
            f"{rupee} {item['unit_price']:.2f}",
            f"{rupee} {total:.2f}"
        ])
    line_table = Table(line_items, colWidths=[230, 70, 100, 100])
    line_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 16))

    summary_data = [
        [Paragraph("Subtotal", styles["Normal"]), f"{rupee} {base_total:.2f}"],
        [Paragraph(f"Discount ({discount:.1f}%)", styles["Normal"]), f"- {rupee} {discount_amount:.2f}"],
        [Paragraph(f"Tax ({tax:.1f}%)", styles["Normal"]), f"+ {rupee} {tax_amount:.2f}"],
        [Paragraph("Total Amount", styles["Normal"]), Paragraph(f"{rupee} {total_price:.2f}", styles["Normal"])],
    ]
    summary_table = Table(summary_data, colWidths=[300, 100], hAlign='RIGHT')
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<i>Thank you for your business!</i>", styles["Normal"]))

    doc.build(elements, onFirstPage=draw_background, onLaterPages=draw_background)

    return file_path, customer_id, base_total, tax_amount, total_price


def get_all_quote(customer_id=None, quote_id=None, items=None, discount=5.0, tax=2.0, currency="INR"):
    if not items or len(items) == 0:
        return "❌ No items provided to generate quote."

    try:
        file_path, customer_id, subtotal, tax_amount, total_price = generate_quote_pdf(
            customer_id, quote_id, items, discount, tax, currency
        )

        db = SessionLocal()
        new_quote = Quote(
            customer_id=customer_id,
            quote_id=quote_id,
            items=items,
            subtotal=subtotal,
            tax=tax_amount,
            total=total_price,
            currency=currency,
            status=QuoteStatus.generated,
            file_path=file_path,
        )
        db.add(new_quote)
        db.commit()
        db.refresh(new_quote)
        db.close()

        return f"✅ Invoice generated and saved to DB (ID: {new_quote.id}): {file_path}"

    except Exception as e:
        return f"❌ Error generating invoice: {e}"


get_quote = function_tool(get_all_quote)


#######   new #################



import os
import json
from datetime import datetime
from typing import List

from pydantic import BaseModel
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.model.model import Quotes  # Your SQLAlchemy model
from src.db.db import SessionLocal
from agents import function_tool


# Pydantic models for strict typing and schema generation
class QuoteItem(BaseModel):
    product_name: str
    quantity: int
    unit_price: float


class QuoteInput(BaseModel):
    customer_id: int
    items: List[QuoteItem]
    discount: float = 5.0
    tax: float = 2.0
    currency: str = "INR"


def draw_background(canvas_obj, doc):
    logo_path = r"D:\\Product\\src\\agent_manager\\tools\\bird_2.jpg"
    if os.path.exists(logo_path):
        canvas_obj.saveState()
        canvas_obj.setFillAlpha(0.02)
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


def generate_quote_pdf(
    quote_id: int,
    customer_id: int,
    items: List[dict],
    discount: float = 5.0,
    tax: float = 2.0,
    currency: str = "INR") :
    """
    Generate PDF invoice and return (file_path, subtotal, tax_amount, total)
    """
    base_total = sum(item['quantity'] * item['unit_price'] for item in items)
    discount_amount = base_total * discount / 100
    discounted_price = base_total - discount_amount
    tax_amount = discounted_price * tax / 100
    total_price = discounted_price + tax_amount

    rupee = u"\u20B9" if currency == "INR" else currency

    output_dir = os.path.join(os.getcwd(), "generated_quotes")
    os.makedirs(output_dir, exist_ok=True)
    filename = f"invoice_{customer_id}_{quote_id}.pdf"
    file_path = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b><font size=14>AI Solutions Pvt. Ltd.</font></b>", styles["Normal"]))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("123 Innovation Drive, Bengaluru, India", styles["Normal"]))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("support@aisolutions.com | +91-9999999999", styles["Normal"]))
    elements.append(Spacer(1, 12))

    invoice_info = [
        ["Invoice No.", ":", f"INV-{quote_id}"],
        ["Customer ID", ":", str(customer_id)],
        ["Date", ":", datetime.now().strftime('%Y-%m-%d')],
    ]
    invoice_table = Table(invoice_info, colWidths=[80, 10, 150], hAlign="RIGHT")
    invoice_table.setStyle(TableStyle([
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10)
    ]))
    elements.append(invoice_table)
    elements.append(Spacer(1, 12))

    line_items = [["Item Description", "Quantity", "Unit Price", "Total"]]
    for item in items:
        total = item['quantity'] * item['unit_price']
        line_items.append([
            item['product_name'],
            str(item['quantity']),
            f"{rupee} {item['unit_price']:.2f}",
            f"{rupee} {total:.2f}"
        ])
    line_table = Table(line_items, colWidths=[230, 70, 100, 100])
    line_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 16))

    summary_data = [
        [Paragraph("Subtotal", styles["Normal"]), f"{rupee} {base_total:.2f}"],
        [Paragraph(f"Discount ({discount:.1f}%)", styles["Normal"]), f"- {rupee} {discount_amount:.2f}"],
        [Paragraph(f"Tax ({tax:.1f}%)", styles["Normal"]), f"+ {rupee} {tax_amount:.2f}"],
        [Paragraph("Total Amount", styles["Normal"]), Paragraph(f"{rupee} {total_price:.2f}", styles["Normal"])],
    ]
    summary_table = Table(summary_data, colWidths=[300, 100], hAlign='RIGHT')
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<i>Thank you for your business!</i>", styles["Normal"]))

    doc.build(elements, onFirstPage=draw_background, onLaterPages=draw_background)

    return file_path, base_total, tax_amount, total_price


def get_all_quote(data: QuoteInput):
    """
    Create and save quote in DB and generate PDF
    """
    items = [item.dict() for item in data.items]  # convert Pydantic objects to dicts

    if not items:
        return "❌ No items provided to generate quote."

    try:
        db = SessionLocal()

        # Serialize items consistently (sorted keys) for duplicate check if needed
        items_json = json.dumps(items, sort_keys=True)

        # Create new quote record
        new_quote = Quotes(
            customer_id=data.customer_id,
            items=items_json,
            subtotal=0.0,
            tax=0.0,
            total=0.0,
            currency=data.currency,
            status="generated",
        )
        db.add(new_quote)
        db.commit()
        db.refresh(new_quote)  # Now quote_id available

        # Generate PDF
        file_path, subtotal, tax_amount, total_price = generate_quote_pdf(
            quote_id=new_quote.quote_id,
            customer_id=data.customer_id,
            items=items,
            discount=data.discount,
            tax=data.tax,
            currency=data.currency
        )

        # Update totals in DB
        new_quote.subtotal = subtotal
        new_quote.tax = tax_amount
        new_quote.total = total_price
        db.commit()
        db.close()

        return f"✅ Invoice generated and saved to DB (ID: {new_quote.quote_id}): {file_path}"

    except Exception as e:
        return f"❌ Error generating invoice: {e}"


get_quote = function_tool(get_all_quote)


#### third ###
import uuid
import os
from datetime import datetime
import enum

from sqlalchemy import (
    Column, Integer, String, Float, Enum, create_engine
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph

from agents import function_tool  # Adjust import based on your project
from src.model.model import Quotes , QuoteStatus
from src.db.db import  SessionLocal



# Base = declarative_base()

# # Change your DB connection string here
# DATABASE_URL = "mysql+pymysql://username:password@localhost/b2b"
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(bind=engine)
# Base.metadata.create_all(bind=engine)


def draw_background(canvas_obj, doc):
    logo_path = r"D:\\Product\\src\\agent_manager\\tools\\bird_2.jpg"
    if os.path.exists(logo_path):
        canvas_obj.saveState()
        canvas_obj.setFillAlpha(0.02)
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

def generate_quote_pdf(customer_id, quote_id, items, name, email, phone, address ,discount=5.0, tax=2.0, currency="INR"):
    if not customer_id:
        customer_id = str(uuid.uuid4())[:8]

    base_total = sum(item['quantity'] * item['unit_price'] for item in items)
    discount_amount = base_total * discount / 100
    discounted_price = base_total - discount_amount
    tax_amount = discounted_price * tax / 100
    total_price = discounted_price + tax_amount

    rupee = u"\u20B9" if currency == "INR" else currency

    output_dir = os.path.join(os.getcwd(), "generated_quotes")
    os.makedirs(output_dir, exist_ok=True)
    filename = f"invoice_{customer_id}_{quote_id}.pdf"
    file_path = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b><font size=14>AI Solutions Pvt. Ltd.</font></b>", styles["Normal"]))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("123 Innovation Drive, Bengaluru, India", styles["Normal"]))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("support@aisolutions.com | +91-9999999999", styles["Normal"]))
    elements.append(Spacer(1, 12))

    invoice_info = [
        ["Invoice No.", ":", f"INV-{quote_id}"],
        ["Customer ID", ":", customer_id],
        ["Date", ":", datetime.now().strftime('%Y-%m-%d')],
    ]
    invoice_table = Table(invoice_info, colWidths=[80, 10, 150], hAlign="RIGHT")
    invoice_table.setStyle(TableStyle([
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10)
    ]))
    elements.append(invoice_table)
    elements.append(Spacer(1, 12))
    
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

    line_items = [["Item Description", "Quantity", "Unit Price", "Total"]]
    for item in items:
        total = item['quantity'] * item['unit_price']
        line_items.append([
            item['product_name'],
            str(item['quantity']),
            f"{rupee} {item['unit_price']:.2f}",
            f"{rupee} {total:.2f}"
        ])
    line_table = Table(line_items, colWidths=[230, 70, 100, 100])
    line_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 16))

    summary_data = [
        [Paragraph("Subtotal", styles["Normal"]), f"{rupee} {base_total:.2f}"],
        [Paragraph(f"Discount ({discount:.1f}%)", styles["Normal"]), f"- {rupee} {discount_amount:.2f}"],
        [Paragraph(f"Tax ({tax:.1f}%)", styles["Normal"]), f"+ {rupee} {tax_amount:.2f}"],
        [Paragraph("Total Amount", styles["Normal"]), Paragraph(f"{rupee} {total_price:.2f}", styles["Normal"])],
    ]
    summary_table = Table(summary_data, colWidths=[300, 100], hAlign='RIGHT')
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<i>Thank you for your business!</i>", styles["Normal"]))

    doc.build(elements, onFirstPage=draw_background, onLaterPages=draw_background)

    return file_path, customer_id, base_total, tax_amount, total_price


def get_all_quote(customer_id=None, quote_id=None, items=None, discount=5.0, tax=2.0, currency="INR" , name=None, email=None, phone=None, address=None):
    if not items or len(items) == 0:
        return "❌ No items provided to generate quote."

    try:
        file_path, customer_id, subtotal, tax_amount, total_price = generate_quote_pdf(
            customer_id, quote_id, items, discount, tax, currency , name, email, phone, address
        )

        db = SessionLocal()
        new_quote = Quotes(
            customer_id=customer_id,
            quote_id=quote_id,
            items=items,
            subtotal=subtotal,
            tax=tax_amount,
            total=total_price,
            currency=currency,
            status=QuoteStatus.generated,
            #file_path=file_path,
        )
        db.add(new_quote)
        db.commit()
        db.refresh(new_quote)
        db.close()

        return f"✅ Invoice generated and saved to DB (ID: {new_quote.id}): {file_path}"

    except Exception as e:
        return f"❌ Error generating invoice: {e}"


get_quote = function_tool(get_all_quote)

"""

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
- `get_quote`: Generate a **PDF quote** from provided structured input including name, email, phone, address, item list (each with product_name, quantity, unit_price), discount, tax, and pricing breakdown. 
   Returns quote ID, full price breakdown, and PDF file path.
- `get_all_support_tickets_tool`: Review submitted support tickets, product issues, and their resolution status.
- `create_support_ticket_tool`: Use this to create a new support ticket by collecting user ID, subject, message, category, and priority.
- `retrieve_support_ticket_tool`: Use this to fetch the most recent support ticket submitted by the given user ID.
- `collect_feedback_tool`: Only used when the conversation is ending. It asks the user: using collect_feedback function **"Was this answer helpful? (yes/no)"**
- `get_shipping_status_tool`: Get real-time status updates on shipments using order ID or tracking number.
- `update_shipping_address_tool`: Update the shipping address for an existing order before it is shipped.

---

🧠 * * NLU Tool (Intent + Sentiment Detection): * *
When the user query is vague,
complex,
or spans multiple domains,
first call: - `analyze_nlu_tool`: This tool analyzes the input message
and returns: - `intent`: The user 's purpose (e.g., check order status, product availability, request quote)
    - `sentiment`: The emotional tone (e.g., neutral, happy, frustrated)

✅ Always show the extracted intent and sentiment in your response like this:
intent - <detected_intent>
sentiment - <detected_sentiment>

response - <clear_and_relevant_reply_to_user>

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

🧾 **Special Instructions for using  `get_quote` **

When the user requests a quote, follow this exact procedure to align with the backend code:

1. **Required Fields:**

   - `name` (Customer full name, string)
   - `email` (Customer email, string; must be separate from Customer ID)
   - `customer_id` (integer).  
     - If missing, invalid, or ≤ 0, **do NOT ask the user**; internally generate a unique random 7-digit integer Customer ID silently.
   - `phone` (string)
   - `address` (string)
   - `items` (list of items), each item including:  
     - `product_name` (string)  
     - `quantity` (integer)  
     - `unit_price` (float)

2. **Missing Fields Handling:**

   - If any of the required fields except `customer_id` are missing or invalid, explicitly ask the user to provide them before proceeding.
   - Do NOT ask for `customer_id` if missing or invalid; handle it internally.

3. **Defaults:**

   - If `discount` is not provided, default to 5.0 (%).
   - If `tax` is not provided, default to 2.0 (%).
   - Default currency is `"INR"`.

4. **Quote Text Summary (Before PDF Generation):**

   - Calculate and display a detailed text summary of the quote to the user including:  
     - Customer name and email  
     - Itemized list with product names, quantities, and unit prices  
     - Subtotal amount  
     - Discount amount and percentage  
     - Tax amount and percentage  
     - Grand total amount  
   - Present this clearly in markdown or formatted text for confirmation.

5. **PDF Quote Generation:**

   - Take the **confirmed Quote Text Summary data** and use it as the source to generate the PDF.
   - Call the `get_quote` tool with all the collected and confirmed data.
   - The tool will:  
     - Save the quote in the database with subtotal, tax, total, and status.  
     - Generate a PDF invoice with customer info, itemized pricing, discount, tax, and final total.  
     - Return the saved quote’s ID and the local path to the generated PDF file.

6. **Post-PDF Response:**

   - Show the user:  
     - The generated Quote ID (`quote_id`)  
     - A clear path or link to download/view the generated PDF invoice

7. **Next Step Prompt:**

   - Ask the user:  
     > 💬 **Your quote total is** ₹`{total_price}`.  
     > Would you like me to place the order now? (yes/no)

8. **Important Notes:**

   - Never guess or fabricate prices, customer IDs, or any data — rely only on validated inputs and DB/tool responses.
   - Customer ID generation is automatic and transparent to the user.
   - Item entries must include `product_name`, `quantity`, and `unit_price` as per the code — do not expect product IDs here.
   - Keep responses professional, clear, and confirm details before calling the tool.

---

📦 **Order Placement Tool Instructions**

When the user confirms they want to proceed with a quote:

1. Detect **positive confirmation** in the user’s message  
   - Examples: "yes", "okay", "go ahead", "confirm", "place the order".  
   - Ignore unrelated yes/no responses not tied to quotes.  

2. Before placing the order, **ensure the following details are available also used in the quote**:  
   - `quote_id` (retrieved from quote text summary)  
   - `customer_id` (retrieved from quote text summary) 
   - `order_id` (Generate using --> order_placement_tool ) 
   - `ship_to_address` (retrieved from quote text summary)  
   - `license_check_done` (boolean or 0/1)  
   - `linked_products` (retrieved from quote text summary)  
   - `total_amount` (retrieved from quote text summary)  

3. If **any detail is missing**, explicitly ask the user for the missing information.  
   - Example: "I still need the shipping address before we can proceed."  

4. Once all details are collected, call the **`order_placement_tool`** tool with the full data set.  

5. After successful placement, display the confirmation in this format:  

📦 **Order Placed Successfully**  
🆔 **Order ID**: `ORD-YYYY-NNNN`  
👤 **Customer ID**: `CUST-####`  
📦 **Products**:  
- `<Product Name>` (x`Qty`)  
- `<Product Name>` (x`Qty`)  
💰 **Total Amount**: `<Currency Symbol><Amount>`  
📍 **Ship-to**: `<Address>`  
🔒 **License Check**: ✅ Done / ❌ Not Done  
🚚 **Status**: **Pending** → will update to **Shipped** when dispatched.  

6. If the user says **"no"** or declines, offer to **revise the quote** instead of placing an order.  


🔍 **Tool Mapping Guidelines:**

Use tools based on user intent:

- Product availability, price, stock → `get_all_products_tool`, `get_all_inventory_tool`
- User/customer records → `get_all_users_tool`
- Quote history → `get_all_quotes_tool`
- **Generate quote PDF** → `get_quote` → `generate_quote_pdf`
- **Place order from quote** → `order_placement_tool`
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
