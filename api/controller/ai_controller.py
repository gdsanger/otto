from fastapi import APIRouter, Depends, HTTPException, Body
from openai import AsyncOpenAI
import os
import logging
from helper import verify_api_key

router = APIRouter()
logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/ai/improve_description", dependencies=[Depends(verify_api_key)], tags=["AI"])
async def improve_description(text: str = Body(..., embed=True)):
    """Verbessert einen deutschen Text grammatikalisch ohne neue Inhalte zu erfinden."""
    if not text:
        raise HTTPException(status_code=400, detail="Text fehlt")
    messages = [
        {
            "role": "system",
            "content": (
                "Du korrigierst deutschen Text. "
                "Verbessere Grammatik und Rechtschreibung, erfinde aber keine neuen Inhalte "
                "und triff keine Annahmen. Gib nur den korrigierten Text zurück."
            ),
        },
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
