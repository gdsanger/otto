# mongo.py - MongoDB-Verbindung und Sammlungshandling
# Verwaltet Zugriff auf Projekte, Personen, Besprechungen und Termine
# (c) Christian Angermeier 2025

from motor.motor_asyncio import AsyncIOMotorClient
from model.projekt import Projekt
from model.person import Person
from model.meeting import Meeting
from pymongo.collection import Collection

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.otto  # DB-Name
projekte_collection = db.projekte
personen_collection = db.personen
# besprechungen_collection = db.besprechungen
# termine_collection = db.termine
meeting_collection = db.meeting

def get_tagesplan_collection() -> Collection:
    return db["tagesplaene"]