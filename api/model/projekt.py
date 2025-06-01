# model.py – Teil des Otto KI-Systems
# © Christian Angermeier 2025

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Literal
from datetime import datetime, date

class Projekt(BaseModel):
    name: str
    short: Optional[str]
    klassifikation: str
    typ: Optional[str] = None
    status: str
    prio: Optional[str] = Field(
        "🟢 normal",
        description="Projektpriorität (z.B. 'hoch', 'mittel', 'niedrig')",
    )
    bearbeiter: Optional[str] = Field(None, description="Verknüpfung zu Personen ID")
    devops_project_id: Optional[str] = Field(
        default=None,
        title="Azure DevOps Project ID ",
        description="Die eindeutige ID des verknüpften DevOps-Projekts"
    )
    geplante_fertigstellung: Optional[str] = None    
    beschreibung: Optional[str] = None
    stakeholder_ids: Optional[List[str]] = []  

class ProjektListe(BaseModel):
    projekte: List[Projekt]
