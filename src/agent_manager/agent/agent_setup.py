from agents import Agent , handoff
from src.agent_manager.prompts.prompt import system_prompt 
from src.agent_manager.tools.user_validation import get_all_users_and_check_tool
from src.agent_manager.tools.tool import get_all_products_tool, get_all_inventory_tool
from src.agent_manager.tools.tool import get_all_quotes_tool, get_all_orders_tool, get_all_leads_tool, get_all_support_tickets_tool
from src.agent_manager.tools.nlu_tools import get_all_nlu_tool
from src.agent_manager.tools.generate_quotes import get_quote
from src.agent_manager.tools.tool import feedback_tool_func
from src.agent_manager.tools.support_ticket_tool import create_support_ticket_tool, retrieve_support_ticket_tool
from src.agent_manager.tools.technical_ans import get_qa_tool
from src.agent_manager.tools.shipping_calculator import get_shipping_status_tool
from src.agent_manager.tools.leads_qualification import get_lead_qual_tool
from src.agent_manager.tools.order_assistant import order_placement_tool
from src.agent_manager.tools.compliance_filter import place_order_tool_func
#from src.agent_manager.tools.tool import detect_intent_and_sentiment
# from src.agent_manager.prompts import neel.md
import os
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path

# Read markdown file into a string
# prompt_path = Path("D:/Product/src/agent_manager/prompts/neel.md")
# system_prompt = prompt_path.read_text(encoding="utf-8")

gemini_api_key = os.environ.get("GEMINI_API_KEY")

model_name = "litellm/gemini/gemini-2.5-flash"

product_inventory_agent = Agent(
    name="product_manager",
    instructions=system_prompt,
    model=model_name,
    tools=[get_all_users_and_check_tool,get_all_inventory_tool, get_all_products_tool,
           get_all_quotes_tool, get_all_orders_tool, get_all_leads_tool, get_all_support_tickets_tool,
           get_all_nlu_tool, get_quote,feedback_tool_func,
           create_support_ticket_tool, retrieve_support_ticket_tool,
           get_qa_tool, get_shipping_status_tool,get_lead_qual_tool,
           order_placement_tool,place_order_tool_func
           ]
           
) 
# model_name_voice = "litellm/gemini/gemini-2.5-flash-live-preview"

# product_inventory_agent_voice = Agent(
#     name="product_manager_voice",
#     instructions=system_prompt,
#     model=model_name_voice,
#     tools=[get_all_users_and_check_tool,get_all_inventory_tool, get_all_products_tool,
#            get_all_quotes_tool, get_all_orders_tool, get_all_leads_tool, get_all_support_tickets_tool,
#            get_all_nlu_tool, get_quote,feedback_tool_func,
#            create_support_ticket_tool, retrieve_support_ticket_tool,
#            get_qa_tool, get_shipping_status_tool,get_lead_qual_tool,
#            order_placement_tool,place_order_tool_func
#            ]
#     )

# root_agent = Agent(
#     name="main_product_agent",
#     instructions="You are able to understand both agent task like if user asked query as a writing and voice",
#     model=model_name,
#     handoffs=[
#         handoff(product_inventory_agent),
#         handoff(product_inventory_agent_voice),
#     ]
# )