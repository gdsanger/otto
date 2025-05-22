# model.py – Teil des Otto KI-Systems
# © Christian Angermeier 2025

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Literal
from datetime import datetime, date

class Message(BaseModel):
    message_id: str
    subject: str
    body: str
    sender: str
    recipient: str
    date: datetime
    direction: str  # "in" oder "out"
    projekt_id: Optional[str] = None
    aufgabe_id: Optional[str] = None