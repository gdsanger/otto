from fastapi import FastAPI, Depends, Header, Request, HTTPException, status, Body, Query, APIRouter
from model.meeting import Meeting
from model.projekt import Projekt, ProjektListe
from model.aufgabe import Aufgabe
from typing import List
from datetime import date
from helper import verify_api_key, serialize_mongo, ensure_folder_exists
from bson import ObjectId
from email import policy
from email.parser import BytesParser
from mongo import projekte_collection, personen_collection, sprints_collection
import logging

router = APIRouter()

@router.get("/projekte/", dependencies=[Depends(verify_api_key)], tags=["Projekt"])
async def lade_projekte():
    logging.info("GET /projekte wurde aufgerufen")
    cursor = projekte_collection.find()
    daten = []

    async for projekt in cursor:
        projekt_dict = serialize_mongo(projekt)

        if "stakeholder_ids" in projekt_dict and projekt_dict["stakeholder_ids"]:
            ids = [ObjectId(pid) for pid in projekt_dict["stakeholder_ids"]]
            personen_cursor = personen_collection.find({"_id": {"$in": ids}})
            stakeholder = []
            async for p in personen_cursor:
                stakeholder.append({
                    "id": str(p["_id"]),
                    "name": p.get("name"),
                    "email": p.get("email"),
                    "mandant": p.get("mandant"),
                    "position": p.get("position")
                })
            projekt_dict["stakeholder"] = stakeholder
        else:
            projekt_dict["stakeholder"] = []

        sprints_cursor = sprints_collection.find({"projekt_id": projekt_dict["id"]})
        projekt_dict["sprints"] = [serialize_mongo(s) async for s in sprints_cursor]

        daten.append(projekt_dict)
    return daten

@router.get("/projekte/{projekt_id}", dependencies=[Depends(verify_api_key)], tags=["Projekt"])
async def get_projekt(projekt_id: str):
    try:
        oid = ObjectId(projekt_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Ungültige Projekt-ID")
   
    projekt = await projekte_collection.find_one({"_id": oid})

    if not projekt:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    projekt_dict = serialize_mongo(projekt)

    if projekt_dict.get("stakeholder_ids"):
        ids = [ObjectId(pid) for pid in projekt_dict["stakeholder_ids"]]
        cursor = personen_collection.find({"_id": {"$in": ids}})
        projekt_dict["stakeholder"] = [serialize_mongo(p) async for p in cursor]
    else:
        projekt_dict["stakeholder"] = []

    sprints_cursor = sprints_collection.find({"projekt_id": projekt_id})
    projekt_dict["sprints"] = [serialize_mongo(s) async for s in sprints_cursor]

    return projekt_dict

@router.post("/projekte/", dependencies=[Depends(verify_api_key)], tags=["Projekt"])
async def speichere_projekte(projekt_liste: ProjektListe = Body(...)):
    logging.info("POST /projekte wurde aufgerufen")

    for projekt in projekt_liste.projekte:
        await ensure_folder_exists(projekt.short)
        for pid in projekt.stakeholder_ids:
            if not await personen_collection.find_one({"_id": ObjectId(pid)}):
                raise HTTPException(status_code=400, detail=f"Ungültige Personen-ID: {pid}")

    result = await projekte_collection.insert_many([p.dict() for p in projekt_liste.projekte])   
    inserted_ids = [str(i) for i in result.inserted_ids]
    
    return {"inserted_ids": inserted_ids}

@router.put("/projekte/{projekt_id}", dependencies=[Depends(verify_api_key)], tags=["Projekt"])
async def update_projekt(projekt_id: str, projekt: Projekt):
    try:
        oid = ObjectId(projekt_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Ungültige ID")

    for pid in projekt.stakeholder_ids:
        if not await personen_collection.find_one({"_id": ObjectId(pid)}):
            raise HTTPException(status_code=400, detail=f"Ungültige Personen-ID: {pid}")
    
    result = await projekte_collection.replace_one({"_id": oid}, projekt.dict())
    await ensure_folder_exists(projekt.short)
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    return {"status": "aktualisiert"}

@router.delete("/projekte/{projekt_id}", dependencies=[Depends(verify_api_key)], tags=["Projekt"])
async def delete_projekt(projekt_id: str):
    try:
        oid = ObjectId(projekt_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Ungültige ID")

    result = await projekte_collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    return {"status": "gelöscht"}