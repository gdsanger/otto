from fastapi import FastAPI, Depends, Header, Request, HTTPException, status, Body, Query, APIRouter
from model.person import PersonenListe, Person
from mongo import personen_collection
from bson import ObjectId
from helper import verify_api_key, serialize_mongo
from pydantic import BaseModel
import logging
router = APIRouter()


@router.get("/personen/", dependencies=[Depends(verify_api_key)], tags=["Personen"])
async def lade_personen():
    logging.info("GET /personen wurde aufgerufen")
    cursor = personen_collection.find()
    daten = [serialize_mongo(p) async for p in cursor]
    return daten

@router.post("/personen/", dependencies=[Depends(verify_api_key)], tags=["Personen"])
async def speichere_personen(personen: PersonenListe = Body(...)):
    logging.info("POST /personen wurde aufgerufen")
    result = await personen_collection.insert_many([p.dict() for p in personen.personen])
    inserted_ids = [str(i) for i in result.inserted_ids]
    return {"inserted_ids": inserted_ids}

# UPDATE-personen (komplett überschreiben)
@router.put("/personen/{person_id}",dependencies=[Depends(verify_api_key)], tags=["Personen"])
async def update_person(person_id: str, person: Person):
    try:
        oid = ObjectId(person_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Ungültige ID")

    result = await personen_collection.replace_one({"_id": oid}, person.dict())
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    return {"status": "aktualisiert"}

# DELETE-personen
@router.delete("/personen/{person_id}", dependencies=[Depends(verify_api_key)], tags=["Personen"])
async def delete_person(person_id: str):
    try:
        oid = ObjectId(person_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Ungültige ID")

    result = await personen_collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    return {"status": "gelöscht"}

