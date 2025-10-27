from agents import function_tool
from typing import Dict

def place_order_tool(age: int) -> Dict[str, str]:
    """
    Places an order only if the user age is >= 16.
    Otherwise, blocks order placement.

    Args:
        age (int): The age of the user.

    Returns:
        Dict[str, str]: A dictionary with two keys: "success" (bool) and "message" (str).
    """
    if age < 16:
        return {"success": False, "message": "❌ Order not allowed. Minimum age is 16."}
    else:
        return {"success": True, "message": "✅ Age verified. Order can be placed."}

place_order_tool_func = function_tool(place_order_tool)