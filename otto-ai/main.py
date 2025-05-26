from fastapi import FastAPI, Request, Query
from pydantic import BaseModel
from openai import OpenAI
from pathlib import Path
import json
import os
import requests
from dotenv import load_dotenv
import re

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OTTO_API_KEY = "6Gri7QQEFh9.1vzDjnbzlGATXJrymoD8"
OTTO_API_URL = "https://data.isarlabs.de/"

app = FastAPI()

class ChatRequest(BaseModel):
    messages: list[dict]

def load_function_templates(type: str):
    base_dir = Path(__file__).parent / "function_call_templates" / type.lower()
    if not base_dir.exists():
        print(f"[WARNUNG] Kein Funktionsverzeichnis gefunden: {base_dir}")
        return []

    tools = []
    for file in base_dir.glob("*.json"):
        try:
            with file.open(encoding="utf-8") as f:
                tools.append(json.load(f))
        except Exception as e:
            print(f"[FEHLER] Fehler beim Laden von {file.name}: {e}")
    return tools

@app.get("/template")
def get_templates(type: str = Query(...)):
    base_dir = Path(__file__).parent / "./function_call_templates" / type
    if not base_dir.exists():
        return [f"Pfad nicht gefunden: {base_dir}"]

    templates = []
    for file in base_dir.glob("*.json"):
        with file.open(encoding="utf-8") as f:
            data = json.load(f)
            if "function" in data and "name" in data["function"]:
                templates.append(data["function"]["name"])

    return templates


@app.post("/chat")
async def chat(request: ChatRequest):
    print(f"Received request: {request}")
    request_messages = request.messages

    # Nachrichten bereinigen
    cleaned_messages = [m for m in request_messages if isinstance(m.get("content"), str)]

    # Kontexttyp aus Systemprompt extrahieren
    system_msg = next((m for m in cleaned_messages if m["role"] == "system"), {})
    ctx_type = "global"
    if "content" in system_msg:
        match = re.search(r"Kontext\s?(\w+)", system_msg["content"])
        if match:
            ctx_type = match.group(1).lower()

    tools = load_function_templates(ctx_type)

    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=cleaned_messages,
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message
    print(f"Message: {message}")

    if message.tool_calls:
        for call in message.tool_calls:
            print(f"Tool call detected: {call.function.name}")
            name = call.function.name
            args = json.loads(call.function.arguments)
            result = await call_function_and_respond(name, args, cleaned_messages, call)
            return result

    return {"reply": message.content}


async def call_function_and_respond(name, args, messages, tool_call):
    if name == "get_project_by_id":
        url = f"{OTTO_API_URL}projekte/{args.get('project_id')}"
    elif name == "get_tasks_of_project":
        url = f"{OTTO_API_URL}project/{args.get('project_id')}/tasks"
    else:
        return {"reply": f"Unbekannte Funktion: {name}"}

    api_response = requests.get(url, headers={"x-api-key": OTTO_API_KEY})

    try:
        result = api_response.json()
    except Exception as e:
        result = {
            "url:": url,
            "error": f"Fehler beim JSON-Parsing: {str(e)}",
            "status_code": api_response.status_code,
            "text": api_response.text
        }
   
    print(f"API response: {result}")

    follow_up = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            *messages,
            {
                "role": "system",
                "content": "Antworte ausschließlich basierend auf der Funktionsausgabe. Keine Ergänzungen, keine Fantasieinformationen."
            },
            {
                "role": "assistant",
                "tool_calls": [  # <- wichtig!
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": name,
                            "arguments": json.dumps(args)
                        }
                    }
                ]
            },
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            }
        ]
    )

    return {"reply": follow_up.choices[0].message.content}




class ProjectRequest(BaseModel):
    project_id: str
