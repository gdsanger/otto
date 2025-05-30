from chromadb import HttpClient

client = HttpClient(host="http://localhost:8000")
collection = client.get_or_create_collection("tasks")

results = collection.get()
print(f"🧠 {len(results['ids'])} Einträge in der Collection 'tasks'")
