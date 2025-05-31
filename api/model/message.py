# model.py – Teil des Otto KI-Systems
# © Christian Angermeier 2025

from pydantic import BaseModel, EmailStr
from typing import List, Optional, Literal
from datetime import datetime

class Message(BaseModel):
    """Repräsentiert eine E-Mail Nachricht."""

    datum: datetime
    subject: str
    sender: Optional[EmailStr] = None
    to: List[EmailStr]
    cc: Optional[List[EmailStr]] = None
    message: str  # HTML Inhalt
    direction: Literal["in", "out"]
    status: Literal["gesendet", "neu", "fehler"] = "neu"
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    sprint_id: Optional[str] = None
    message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    attachments: Optional[List[str]] = None
