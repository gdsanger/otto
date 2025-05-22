# model.py – Teil des Otto KI-Systems
# © Christian Angermeier 2025

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Literal
from datetime import datetime, date

class Person(BaseModel):
    name: str
    email: EmailStr
    mandant: str
    position: Optional[str] = None
    anrede: Optional[Literal
    [
        "Du", 
        "Sie"
    ]] = "Du"
    sprache: Optional[Literal[
        "Deutsch",
        "Englisch"
    ]] = "Deutsch"

    rolle: Optional[Literal[
        "user",        # darf eigene Aufgaben sehen / kommentieren
        "agent",       # darf Aufgaben übernehmen / abschließen
        "koordinator", # darf Aufgaben zuweisen, umpriorisieren
        "admin",       # darf System konfigurieren, Rollen ändern
        "otto"         # interne Systemrolle für KI-Aktionen
    ]] = "user"

class PersonenListe(BaseModel):
    personen: List[Person]