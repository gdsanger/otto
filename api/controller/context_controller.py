from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from helper import verify_api_key, serialize_mongo
from mongo import projekte_collection, personen_collection, sprints_collection, db

router = APIRouter()


@router.get("/context/projekt/{projekt_id}", dependencies=[Depends(verify_api_key)], tags=["Context"])
async def projekt_context(projekt_id: str):
    try:
        oid = ObjectId(projekt_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Ungültige Projekt-ID")

    projekt = await projekte_collection.find_one({"_id": oid})
    if not projekt:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    proj_dict = serialize_mongo(projekt)

    if proj_dict.get("bearbeiter"):
        person = await personen_collection.find_one({"_id": ObjectId(proj_dict["bearbeiter"])})
        if person:
            proj_dict["bearbeiter"] = serialize_mongo(person)

    if proj_dict.get("stakeholder_ids"):
        ids = [ObjectId(pid) for pid in proj_dict["stakeholder_ids"]]
        cursor = personen_collection.find({"_id": {"$in": ids}})
        proj_dict["stakeholder"] = [serialize_mongo(p) async for p in cursor]

    tasks_cursor = db.tasks.find({"project_id": projekt_id})
    proj_tasks = []
    async for t in tasks_cursor:
        t_dict = serialize_mongo(t)
        t_dict["context_text"] = await _build_context_text(t_dict)
        proj_tasks.append(t_dict)
    proj_dict["aufgaben"] = proj_tasks

    sprints_cursor = sprints_collection.find({"projekt_id": projekt_id})
    proj_dict["sprints"] = [serialize_mongo(s) async for s in sprints_cursor]

    proj_dict["dateien"] = []

    return proj_dict

@router.get("/context/aufgabe/{aufgabe_id}", dependencies=[Depends(verify_api_key)], tags=["Context"])
async def aufgabe_context(aufgabe_id: str):
    try:
        oid = ObjectId(aufgabe_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Ungültige Aufgabe-ID")

    task = await db.tasks.find_one({"_id": oid})
    if not task:
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")

    task_dict = serialize_mongo(task)

    if task_dict.get("person_id"):
        person = await personen_collection.find_one({"_id": ObjectId(task_dict["person_id"])})
        if person:
            task_dict["person"] = serialize_mongo(person)

    if task_dict.get("project_id"):
        proj = await projekte_collection.find_one({"_id": ObjectId(task_dict["project_id"])})
        if proj:
            proj_dict = serialize_mongo(proj)
            if proj_dict.get("bearbeiter"):
                pb = await personen_collection.find_one({"_id": ObjectId(proj_dict["bearbeiter"])})
                if pb:
                    proj_dict["bearbeiter"] = serialize_mongo(pb)
            if proj_dict.get("stakeholder_ids"):
                ids = [ObjectId(pid) for pid in proj_dict["stakeholder_ids"]]
                cursor = personen_collection.find({"_id": {"$in": ids}})
                proj_dict["stakeholder"] = [serialize_mongo(p) async for p in cursor]
            else:
                proj_dict["stakeholder"] = []
            task_dict["projekt"] = proj_dict


    task_dict["context_text"] = await _build_context_text(task_dict)

    if task_dict.get("sprint_id"):
        sprint = await sprints_collection.find_one({"_id": ObjectId(task_dict["sprint_id"])})
        if sprint:
            task_dict["sprint"] = serialize_mongo(sprint)


    return task_dict

@router.get("/context/person/{person_id}", dependencies=[Depends(verify_api_key)], tags=["Context"])
async def person_context(person_id: str):
    try:
        oid = ObjectId(person_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Ungültige Personen-ID")

    person = await personen_collection.find_one({"_id": oid})
    if not person:
        raise HTTPException(status_code=404, detail="Person nicht gefunden")

    person_dict = serialize_mongo(person)

    tasks_cursor = db.tasks.find({"person_id": person_id})
    tasks = []
    async for t in tasks_cursor:
        t_dict = serialize_mongo(t)
        if t_dict.get("project_id"):
            proj = await projekte_collection.find_one({"_id": ObjectId(t_dict["project_id"])})
            if proj:
                proj_dict = serialize_mongo(proj)
                if proj_dict.get("bearbeiter"):
                    pb = await personen_collection.find_one({"_id": ObjectId(proj_dict["bearbeiter"])})
                    if pb:
                        proj_dict["bearbeiter"] = serialize_mongo(pb)
                if proj_dict.get("stakeholder_ids"):
                    ids = [ObjectId(pid) for pid in proj_dict["stakeholder_ids"]]
                    cursor = personen_collection.find({"_id": {"$in": ids}})
                    proj_dict["stakeholder"] = [serialize_mongo(p) async for p in cursor]
                t_dict["projekt"] = proj_dict
        t_dict["context_text"] = await _build_context_text(t_dict)
        tasks.append(t_dict)

    person_dict["tasks"] = tasks
    return person_dict
