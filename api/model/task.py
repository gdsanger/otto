from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class Task(BaseModel):
    tid: Optional[int] = None
    betreff: str
    beschreibung: Optional[str] = ""
    umsetzung: Optional[str] = ""
    tasktype: Optional[str] = Field(None, description="Typ der Aufgabe, z.B. 'Aufgabe', 'Feature', 'Bug', 'Ticket', 'Requirement', 'Sonstiges'")
    person_id: str = Field(..., description="ID der verantwortlichen Person (personen.id)")
    requester_id: Optional[str] = Field(None, description="ID der anfordernden Person (personen.id)")
    aufwand: int
    notizen: Optional[str] = ""
    prio: Optional[str]  # z.B. "hoch", "mittel", "niedrig"
    typ: Optional[str] = None
    termin: Optional[date] = None
    erledigt: Optional[date] = None
    status: str  # z.B. "offen", "in Arbeit", "erledigt"
    project_id: Optional[str] = None
    sprint_id: Optional[str] = None
    meeting_id: Optional[str] = None
    context_text: Optional[str] = None
