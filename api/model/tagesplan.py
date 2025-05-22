from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class TagesplanAufgabe(BaseModel):
    task_id: Optional[str] = Field(None, description="Verknüpfung zu bestehender Otto-Task, falls vorhanden")
    quelle: str = Field(..., description="'otto' oder 'freestyle'")
    kommentar: str
    aufwand: Optional[float] = Field(None, description="Aufwand in Stunden")
    prio: Optional[str] = Field("mittel", description="'hoch', 'mittel', 'niedrig'")

class Tagesplan(BaseModel):
    datum: date
    person_id: str
    ort: Optional[str]
    fokus: Optional[str]
    aufgaben: List[TagesplanAufgabe] = []
    notizen: Optional[str] = ""
