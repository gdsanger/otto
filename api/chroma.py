"""Helper utilities for synchronizing tasks with ChromaDB."""

from chromadb import PersistentClient
from pathlib import Path
from config import BASE_DIR

# Chroma collections are stored under ``BASE_DIR/chroma``.
client = PersistentClient(path=str(Path(BASE_DIR) / "chroma"))
collection = client.get_or_create_collection("tasks")


def upsert_task(task: dict):
    """Upsert a task document in the Chroma 'tasks' collection."""
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

