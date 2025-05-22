# model.py – Teil des Otto KI-Systems
# © Christian Angermeier 2025

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Literal
from datetime import datetime, date

class Aufgabe(BaseModel):
    beschreibung: str
    zuständig: Optional[str] = None
    zuständig_id: Optional[str] = None
    aufwand: Optional[int] = 0
    notizen: Optional[str] = None
    prio: Optional[str] = None
    termin: Optional[str] | Literal[""] = None
    wiedervorlage: Optional[date] = None
    status: Optional[str] = None