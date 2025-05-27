from pydantic import BaseModel, Field
from typing import List

class Ressource(BaseModel):
    person_id: str = Field(..., description="ID der Person (personen.id)")
    extern: bool = False
    anteil: float = 0.0

class Team(BaseModel):
    name: str
    ressourcen: List[Ressource] = []

class TeamListe(BaseModel):
    teams: List[Team]
