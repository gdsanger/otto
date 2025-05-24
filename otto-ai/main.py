from fastapi import FastAPI, Request
from pydantic import BaseModel
from openai import OpenAI
import os
import requests
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OTTO_API_KEY = os.getenv("OTTO_API_KEY")
OTTO_API_URL = "https://data.isarlabs.de/"

app = FastAPI()

class ChatRequest(BaseModel):
    messages: list[dict]

@app.post("/chat")
async def chat(request: ChatRequest):
    messages = request.messages
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
    message = response.choices[0].message
    return {"reply": message.content}


async def call_function_and_respond(name, args, messages, message):
    if name == "get_project_by_id":
        url = f"{OTTO_API_URL}/projekte/{args.get('project_id')}"
    elif name == "get_tasks_of_project":
        url = f"{OTTO_API_URL}/projekte/{args.get('project_id')}/tasks"
    else:
        return {"reply": f"Unbekannte Funktion: {name}"}

    api_response = requests.post(url, headers={"x-api-key": OTTO_API_KEY})
    result = api_response.json()

    follow_up = client.chat.completions.create(
        model="gpt-4",
        messages = [
            *messages,
            {
                "role": "system",
                "content": "Antworte ausschließlich basierend auf der Funktionsausgabe. Keine Ergänzungen, keine Fantasieinformationen."
            },
            {
                "role": "assistant",
                "function_call": message.function_call
            },
            {
                "role": "function",
                "name": name,
                "content": json.dumps(result)
            }
        ],
    )
    return {"reply": follow_up.choices[0].message.content}



class ProjectRequest(BaseModel):
    project_id: str
