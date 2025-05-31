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
sprints_collection = db.sprints
teams_collection = db.teams
users = db["users"]
messages_collection = db.messages
comments_collection = db.comments
db.meetings.delete_many({"id": ""})

def get_tagesplan_collection() -> Collection:
    return db["tagesplaene"]