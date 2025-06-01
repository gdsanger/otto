from fastapi import APIRouter, Depends, HTTPException, Body
from openai import AsyncOpenAI
import os
import logging
from helper import verify_api_key

router = APIRouter()
logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/ai/improve_description", dependencies=[Depends(verify_api_key)], tags=["AI"])
async def improve_description(payload: dict = Body(...)):
    """Verbessere den folgenden Text nur stilistisch und hinsichtlich Klarheit. Verbessert einen deutschen Text grammatikalisch ohne neue Inhalte zu erfinden."""

    text = (payload.get("text") or "").strip()
    html = bool(payload.get("html"))

    if not text:
        raise HTTPException(status_code=400, detail="Text fehlt")

    system_msg = (
        "Du korrigierst deutschen Text. "
        "Verbessere Grammatik und Rechtschreibung und überarbeite diesen Hinsichtlich Stil und Klaheit, erfinde aber keine neuen Inhalte "
        "und triff keine Annahmen."
    )
    if html:
        system_msg += " Gib den korrigierten Text als HTML zurück."
    else:
        system_msg += " Gib nur den korrigierten Text zurück."

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": text},
    ]

    try:
        resp = await client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=messages,
            temperature=0,
        )
        improved = resp.choices[0].message.content.strip()
    except Exception as e:
        logger.exception("OpenAI request failed: %s", e)
        raise HTTPException(status_code=500, detail="AI request failed")

    return {"text": improved}
