from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from agents import Runner
from agents.run import RunConfig
from src.agent_manager.agent.agent_setup import product_inventory_agent
from src.agent_manager.session.custom_session import MyCustomSession
import uuid
import json

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

sessions = {}

@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ---------- API Endpoint instead of WebSocket ----------
@app.post("/chat")
async def chat_api(request: Request):
    data = await request.json()
    user_input = data.get("message")

    if not user_input:
        return JSONResponse({"error": "Message is required"}, status_code=400)

    # Reuse or create session
    session_id = data.get("session_id") or str(uuid.uuid4())
    if session_id not in sessions:
        sessions[session_id] = MyCustomSession(session_id)

    session = sessions[session_id]
    run_config = RunConfig(tracing_disabled=True)

    try:
        result = await Runner.run(
            product_inventory_agent,
            input=user_input,
            session=session,
            run_config=run_config
        )

        formatted_output = format_agent_response(result.final_output)

        return {
            "session_id": session_id,
            "user_input": user_input,
            "response": formatted_output
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ---------- Response Formatter ----------
def format_agent_response(text: str) -> str:
    import re
    if not text:
        return ""
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)  # bold
    text = re.sub(r"\* ", r"<br>", text)  # newline via "* "
    return text
