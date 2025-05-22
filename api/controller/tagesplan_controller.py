from fastapi import APIRouter, HTTPException, Depends
from datetime import date
from typing import List
from model.tagesplan import Tagesplan
from mongo import get_tagesplan_collection
from helper import verify_api_key, serialize_mongo

router = APIRouter(prefix="/tagesplan", tags=["Tagesplan"])
collection = get_tagesplan_collection()

@router.get("/{datum}", response_model=Tagesplan, dependencies=[Depends(verify_api_key)])
async def get_tagesplan(datum: date, person_id: str):
    doc = await collection.find_one({"datum": datum.isoformat(), "person_id": person_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Kein Tagesplan gefunden")
    return doc

@router.post("/", response_model=Tagesplan, dependencies=[Depends(verify_api_key)])
async def create_tagesplan(plan: Tagesplan):
    doc = plan.dict()
    doc["datum"] = plan.datum.isoformat()
    existing = await collection.find_one({"datum": doc["datum"], "person_id": doc["person_id"]})
    if existing:
        raise HTTPException(status_code=409, detail="Tagesplan für diesen Tag existiert bereits")
    await collection.insert_one(doc)
    return plan

@router.put("/{datum}", response_model=Tagesplan, dependencies=[Depends(verify_api_key)])
async def update_tagesplan(datum: date, person_id: str, plan: Tagesplan):
    doc = plan.dict()
    doc["datum"] = datum.isoformat()
    doc["person_id"] = person_id
    result = await collection.replace_one({"datum": doc["datum"], "person_id": person_id}, doc, upsert=True)
    return plan

@router.delete("/{datum}", dependencies=[Depends(verify_api_key)])
async def delete_tagesplan(datum: date, person_id: str):
    result = await collection.delete_one({"datum": datum.isoformat(), "person_id": person_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Kein Tagesplan gefunden")
    return {"status": "deleted", "datum": datum.isoformat(), "person_id": person_id}