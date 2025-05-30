"""Helper utilities for synchronizing tasks with ChromaDB."""

from chromadb import HttpClient
from pathlib import Path
from config import BASE_DIR


from chromadb import HttpClient
client = HttpClient(host="http://localhost:8000")
collection = client.get_or_create_collection("tasks")

def upsert_task(task: dict):
    """Upsert a task document in the Chroma 'tasks' collection."""
    print(f"⬆️ Upsert Task: {task['id']} – {task['betreff']}")
    print("🧠 Kontext:", task["context_text"][:100])
    collection.upsert(
        documents=[task["context_text"]],
        metadatas=[{
            "projekt": task.get("projekt", {}).get("short"),
            "bearbeiter": task.get("person", {}).get("name"),
            "status": task.get("status"),
            "prio": task.get("prio"),
            "typ": task.get("typ"),
            "full": task,
        }],
        ids=[task["id"]],
    )


def similar_tasks(query_text: str, exclude_id: str, limit: int = 5):
    """Return a list of tasks similar to the given query text.

    Parameters
    ----------
    query_text: str
        Text used as the query for the semantic search.
    exclude_id: str
        ID of the task that initiated the search. The task with this ID is
        excluded from the result list if returned by Chroma.
    limit: int, optional
        Maximum number of similar tasks to return. Defaults to 5.

    Returns
    -------
    list[dict]
        Each dict contains ``id``, ``betreff`` and ``projekt`` keys.
    """

    res = collection.query(
        query_texts=[query_text],
        n_results=limit + 1,
        include=["metadatas"],
    )

    tasks = []
    for task_id, meta in zip(res.get("ids", [[ ]])[0], res.get("metadatas", [[ ]])[0]):
        if task_id == exclude_id:
            continue
        full = meta.get("full", {}) if meta else {}
        tasks.append(
            {
                "id": task_id,
                "betreff": full.get("betreff"),
                "projekt": full.get("projekt", {}).get("name"),
            }
        )
        if len(tasks) >= limit:
            break
    return tasks

