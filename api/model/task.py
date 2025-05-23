from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class Task(BaseModel):
    betreff: str
    beschreibung: Optional[str] = ""
    zuständig: str
    person_id: str = Field(..., description="ID der verantwortlichen Person (personen.id)")
    aufwand: int
    notizen: Optional[str] = ""
    prio: Optional[str]  # z.B. "hoch", "mittel", "niedrig"
    termin: Optional[date] = None
    status: str  # z.B. "offen", "in Arbeit", "erledigt"
    project_id: Optional[str] = None
    meeting_id: Optional[str] = None