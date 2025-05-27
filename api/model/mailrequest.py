# model.py – Teil des Otto KI-Systems
# © Christian Angermeier 2025

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Literal
from datetime import datetime, date

class MailRequest(BaseModel):
    subject: str
    body: str
    to: str
    cc: Optional[str] = None