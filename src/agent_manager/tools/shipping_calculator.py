from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from agents import function_tool

# 🧾 Models
class ShippingStatusRequest(BaseModel):
    quote_id: str
    #total_weight_kg: float
    hazmat_flag: bool = False

class ShippingStatusResponse(BaseModel):
    quote_id: str
    status: str
    estimated_delivery: Optional[str] = None
    last_updated: str
    hazmat_flag: bool = False

# 🚚 Tool logic
def get_shipping_status_function(request: ShippingStatusRequest) -> ShippingStatusResponse:
    current_time = datetime.utcnow()
    quote_id = request.quote_id.strip()

    # Determine ETA dynamically
    base_days = 5
    extra_days = 2 if request.hazmat_flag else 0
    eta_date = current_time + timedelta(days=base_days + extra_days)

    # Simple example status logic
    status = "Shipped" if int(quote_id) % 2 != 0 else "Processing"

    return ShippingStatusResponse(
        quote_id=quote_id,
        status=status,
        estimated_delivery=eta_date.strftime("%Y-%m-%d"),
        last_updated=current_time.strftime("%Y-%m-%d %H:%M:%S"),
        hazmat_flag=request.hazmat_flag,
    )

# 🛠️ Register the tool
get_shipping_status_tool = function_tool(
    get_shipping_status_function,
)
