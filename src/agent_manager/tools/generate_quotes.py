import os
import json
import random
from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.model.model import Quotes  # SQLAlchemy model
from src.db.db import SessionLocal
from agents import function_tool


class QuoteItem(BaseModel):
    product_name: str
    quantity: int
    unit_price: float


class QuoteInput(BaseModel):
    customer_id: int = 0
    name: str
    email: str
    phone: str
    address: str
    items: List[QuoteItem]
    discount: float = 5.0
    tax: float = 2.0
    currency: str = "INR"


from reportlab.lib.utils import ImageReader
import os

def draw_background(canvas_obj, doc):
    logo_path = r"D:\\Product\\src\\agent_manager\\tools\\bird_2.jpg"
    if os.path.exists(logo_path):
        canvas_obj.saveState()

        # Get page size
        page_width, page_height = doc.pagesize

        # Set opacity: 0.05 is faint, 0.15-0.2 is a bit darker but still watermark style
        canvas_obj.setFillAlpha(0.15)

        # Draw full-page image, centered
        canvas_obj.drawImage(
            ImageReader(logo_path),
            x=0,
            y=0,
            width=page_width,
            height=page_height,
            preserveAspectRatio=True,
            mask='auto'
        )

        canvas_obj.restoreState()


def generate_quote_pdf(
    quote_id: int,
    name: str,
    email: str,
    phone: str,
    address: str,
    items: List[dict],
    discount: float = 5.0,
    tax: float = 2.0,
    currency: str = "INR",
    file_path: str = None
):
    if not items:
        raise ValueError("No items provided for PDF generation.")

    rupee = u"\u20B9" if currency == "INR" else currency

    base_total = sum(item['quantity'] * item['unit_price'] for item in items)
    discount_amount = base_total * discount / 100
    discounted_price = base_total - discount_amount
    tax_amount = discounted_price * tax / 100
    total_price = discounted_price + tax_amount

    if not file_path:
        output_dir = os.path.join(os.getcwd(), "generated_quotes")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"invoice_{quote_id}.pdf"
        file_path = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    elements.append(Paragraph("<b><font size=14>AI Solutions Pvt. Ltd.</font></b>", styles["Normal"]))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("123 Innovation Drive, Bengaluru, India", styles["Normal"]))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("support@aisolutions.com | +91-9999999999", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Customer info
    customer_info = [
        ["Customer Name:", name],
        ["Email:", email],
        ["Phone:", phone],
        ["Address:", address],
        ["Invoice No.:", f"INV-{quote_id}"],
        ["Date:", datetime.now().strftime('%Y-%m-%d')],
    ]
    customer_table = Table(customer_info, colWidths=[120, 350])
    customer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(customer_table)
    elements.append(Spacer(1, 16))

    # Items table
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

    # Summary
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
    db = SessionLocal()
    try:
        items: List[dict] = [item.dict() for item in data.items]

        if not items:
            raise ValueError("No items provided to generate quote.")

        if not isinstance(data.customer_id, int) or data.customer_id <= 0:
            data.customer_id = random.randint(1000000, 9999999)

        items_json = json.dumps(items, sort_keys=True)

        new_quote = Quotes(
            customer_id=data.customer_id,
            items=items_json,
            subtotal=Decimal("0.00"),
            tax=Decimal("0.00"),
            total=Decimal("0.00"),
            currency=data.currency,
            status="generated",
        )
        db.add(new_quote)
        db.commit()
        db.refresh(new_quote)

        output_dir = r"D:\B2B-AGENT\Invoices"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        custom_path = os.path.join(output_dir, f"invoice_{new_quote.quote_id}_{timestamp}.pdf")

        file_path, subtotal, tax_amount, total_price = generate_quote_pdf(
            quote_id=new_quote.quote_id,
            name=data.name,
            email=data.email,
            phone=data.phone,
            address=data.address,
            items=items,
            discount=data.discount,
            tax=data.tax,
            currency=data.currency,
            file_path=custom_path
        )

        new_quote.subtotal = Decimal(str(subtotal))
        new_quote.tax = Decimal(str(tax_amount))
        new_quote.total = Decimal(str(total_price))
        db.commit()

        return {
            "quote_id": new_quote.quote_id,
            "customer_id": data.customer_id,
            "subtotal": float(subtotal),
            "tax": float(tax_amount),
            "total_price": float(total_price),
            "currency": data.currency,
            "pdf_path": file_path
        }

    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


# Register tool
get_quote = function_tool(get_all_quote)