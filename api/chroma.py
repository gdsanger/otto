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
            "typ": task.get("typ")
        }],
        ids=[task["id"]],
    )

