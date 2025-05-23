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
meeting_collection = db.meeting
users = db["users"]
db.meetings.delete_many({"id": ""})

def get_tagesplan_collection() -> Collection:
    return db["tagesplaene"]