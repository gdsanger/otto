from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date

class Sprint(BaseModel):
    name: str
    projekt_id: str = Field(..., description="ID des zugehörigen Projekts")
    typ: Literal['minor', 'major']
    startdatum: date
    enddatum: date
    beschreibung: Optional[str] = None
    status: Literal['neu', 'aktiv', 'abgeschlossen']

class SprintListe(BaseModel):
    sprints: list[Sprint]
