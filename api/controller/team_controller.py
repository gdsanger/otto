from fastapi import APIRouter, Depends, HTTPException
from typing import List
from bson import ObjectId
from helper import verify_api_key, serialize_mongo
from mongo import db
from model.team import Team, TeamListe

router = APIRouter()

@router.get("/teams", dependencies=[Depends(verify_api_key)], tags=["Team"])
async def list_teams():
    cursor = db.teams.find()
    return [serialize_mongo(t) async for t in cursor]

@router.get("/teams/{team_id}", dependencies=[Depends(verify_api_key)], tags=["Team"])
async def get_team(team_id: str):
    team = await db.teams.find_one({"_id": ObjectId(team_id)})
    if not team:
        raise HTTPException(status_code=404, detail="Team nicht gefunden")
    return serialize_mongo(team)

@router.post("/teams", dependencies=[Depends(verify_api_key)], tags=["Team"])
async def create_team(team_liste: TeamListe):
    print(f"Teamliste: {team_liste}")
    result = await db.teams.insert_many([t.dict() for t in team_liste.teams])
    return {"inserted_ids": [str(i) for i in result.inserted_ids]}

@router.put("/teams/{team_id}", dependencies=[Depends(verify_api_key)], tags=["Team"])
async def update_team(team_id: str, team: Team):
    result = await db.teams.replace_one({"_id": ObjectId(team_id)}, team.dict())
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Team nicht gefunden")
    return {"status": "aktualisiert"}

@router.delete("/teams/{team_id}", dependencies=[Depends(verify_api_key)], tags=["Team"])
async def delete_team(team_id: str):
    result = await db.teams.delete_one({"_id": ObjectId(team_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Team nicht gefunden")
    return {"status": "gelöscht"}
