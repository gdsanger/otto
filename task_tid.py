from pymongo import MongoClient

# Verbindung zu MongoDB
client = MongoClient("mongodb://localhost:27017")  # ggf. anpassen

db = client["otto"]  # Name der DB anpassen
tasks = db["tasks"]
counters = db["counters"]

# Starte den TID-Zähler bei 1 oder aktuellem Maximalwert
start_tid = 1000

# Bestehende Aufgaben ohne TID holen
existing_tasks = list(tasks.find({"tid": {"$exists": False}}).sort("_id"))

for index, task in enumerate(existing_tasks):
    tid = start_tid + index
    tasks.update_one({"_id": task["_id"]}, {"$set": {"tid": tid}})
    print(f"Updated Task {task['_id']} with tid {tid}")


# Höchsten TID-Wert speichern, damit neue Aufgaben dort weiterzählen
last_tid = start_tid + len(existing_tasks) - 1
counters.update_one(
    {"_id": "task_tid"},
    {"$set": {"seq": last_tid}},
    upsert=True
)

print(f"✅ {len(existing_tasks)} tasks updated. Counter set to {last_tid}.")
