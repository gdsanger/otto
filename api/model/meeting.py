from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class Meeting(BaseModel):
    id: str
    name: str
    beschreibung: Optional[str] = None
    datum: date
    von: str  # z. B. "13:00"
    bis: str  # z. B. "15:00"
    teilnehmer: List[str]  # Personen-IDs    
    themen: Optional[str] # Nachfoger von Agenda als plantext
    mandant: Optional[str] = None