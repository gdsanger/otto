from fastapi import APIRouter, HTTPException, Depends
from typing import List
from model.task import Task
from helper import verify_api_key, serialize_mongo
from mongo import db
from datetime import datetime, date
from bson import ObjectId
from pymongo import ReturnDocument
from controller.context_controller import aufgabe_context
from chroma import upsert_task
import asyncio

router = APIRouter()

async def get_next_tid():
    """Increment and return the next task id.

    The counter document is created on first use with the value ``1000``.
    A pipeline update avoids conflicting update operators when
    the document needs to be initialized and incremented in one step.
    """

    counter = await db.counters.find_one_and_update(
        {"_id": "task_tid"},
        [{"$set": {"seq": {"$add": [{"$ifNull": ["$seq", 999]}, 1]}}}],
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return counter["seq"]

def convert_dates(task_dict):
    for key in ["termin"]:
        if isinstance(task_dict.get(key), date):
            task_dict[key] = datetime.combine(task_dict[key], datetime.min.time())
    return task_dict

@router.get("/tasks", dependencies=[Depends(verify_api_key)], tags=["Task"])
async def list_tasks():
    cursor = db.tasks.find()
    tasks = []
    async for task in cursor:
        t = serialize_mongo(task)
        tasks.append(t)
    return tasks

@router.post("/tasks", dependencies=[Depends(verify_api_key)], tags=["Task"])
async def create_task(task: Task):
    if not await db.personen.find_one({"_id": ObjectId(task.person_id)}):
        raise HTTPException(status_code=400, detail=f"Person mit ID '{task.person_id}' nicht gefunden.")
    if task.requester_id and not await db.personen.find_one({"_id": ObjectId(task.requester_id)}):
        raise HTTPException(status_code=400, detail=f"Requester mit ID '{task.requester_id}' nicht gefunden.")
    if task.sprint_id:
        if not await db.sprints.find_one({"_id": ObjectId(task.sprint_id)}):
            raise HTTPException(status_code=400, detail="Sprint nicht gefunden")

    task_dict = convert_dates(task.dict())
    # "tid" wird von Pydantic immer im Dictionary vorhanden sein.
    # Darum auch dann eine neue TID vergeben, wenn der Wert None ist.
    if task_dict.get("tid") is None:
        task_dict["tid"] = await get_next_tid()

    result = await db.tasks.insert_one(task_dict)
    task_id = str(result.inserted_id)
    try:
        context = await aufgabe_context(task_id)
        await asyncio.to_thread(upsert_task, context)
    except Exception as e:
        print(f"Chroma update failed: {e}")
    return {"status": "ok", "id": task_id}

@router.get("/tasks/{task_id}", response_model=Task, dependencies=[Depends(verify_api_key)], tags=["Task"])
async def get_task(task_id: str):
    try:
        oid = ObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Ungültige ID")

    task = await db.tasks.find_one({"_id": oid})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return serialize_mongo(task)

@router.put("/tasks/{task_id}", dependencies=[Depends(verify_api_key)], tags=["Task"])
async def update_task(task_id: str, task: Task):
    if not await db.personen.find_one({"_id": ObjectId(task.person_id)}):
        raise HTTPException(status_code=400, detail=f"Person mit ID '{task.person_id}' nicht gefunden.")
    if task.requester_id and not await db.personen.find_one({"_id": ObjectId(task.requester_id)}):
        raise HTTPException(status_code=400, detail=f"Requester mit ID '{task.requester_id}' nicht gefunden.")
    if task.sprint_id:
        if not await db.sprints.find_one({"_id": ObjectId(task.sprint_id)}):
            raise HTTPException(status_code=400, detail="Sprint nicht gefunden")

    task_dict = convert_dates(task.dict())
    if task_dict.get("tid") is None:
        # Bei Updates kann "tid" explizit auf None gesetzt sein.
        print("Task TID is None, generating new one")
        task_dict["tid"] = await get_next_tid()

    result = await db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": task_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        context = await aufgabe_context(task_id)
        await asyncio.to_thread(upsert_task, context)
    except Exception as e:
        print(f"Chroma update failed: {e}")

    return {"status": "updated"}

@router.delete("/tasks/{task_id}", dependencies=[Depends(verify_api_key)], tags=["Task"])
async def delete_task(task_id: str):
    result = await db.tasks.delete_one({"_id": ObjectId(task_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "deleted"}

@router.get("/project/{project_id}/tasks", dependencies=[Depends(verify_api_key)], tags=["Projekt"])
async def get_tasks_by_project(project_id: str):
    cursor = db.tasks.find({"project_id": project_id})
    return [serialize_mongo(task) async for task in cursor]

@router.get("/sprint/{sprint_id}/tasks", dependencies=[Depends(verify_api_key)], tags=["Sprint"])
async def get_tasks_by_sprint(sprint_id: str):
    """Return all tasks that belong to the given sprint."""
    cursor = db.tasks.find({"sprint_id": sprint_id})
    return [serialize_mongo(task) async for task in cursor]
