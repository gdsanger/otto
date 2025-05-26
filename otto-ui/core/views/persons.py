import requests
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .helpers import login_required
from core.const import status_liste, prio_liste
import os
from dotenv import load_dotenv

load_dotenv()

OTTO_API_KEY = os.getenv("OTTO_API_KEY")
OTTO_API_URL = os.getenv("OTTO_API_URL")

@login_required
def person_listview(request):
    res = requests.get(f"{OTTO_API_URL}/personen", headers={"x-api-key": OTTO_API_KEY})
    personen = res.json() if res.status_code == 200 else []
    q = request.GET.get("q", "").lower()
    if q:
        personen = [p for p in personen if q in p.get("name", "").lower() or q in p.get("email", "").lower()]
    return render(request, "core/person_listview.html", {"personen": personen})

@login_required
@csrf_exempt
def person_detailview(request, person_id):
    if request.method == "POST":
        payload = json.loads(request.body)
        res = requests.get(f"{OTTO_API_URL}/personen/{person_id}", headers={"x-api-key": OTTO_API_KEY})
        if res.status_code != 200:
            return JsonResponse({"error": "Person nicht gefunden"}, status=404)
        person = res.json()
        for k, v in payload.items():
            person[k] = v
        update = requests.put(
            f"{OTTO_API_URL}/personen/{person_id}",
            headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
            data=json.dumps(person)
        )
        return JsonResponse({"success": True}) if update.status_code == 200 else JsonResponse({"error": "Fehler beim Speichern"}, status=500)

    res = requests.get(f"{OTTO_API_URL}/personen/{person_id}", headers={"x-api-key": OTTO_API_KEY})
    if res.status_code != 200:
        return render(request, "core/person_detailview.html", {"person": {}, "tasks": []})
    data = res.json()
    tasks = data.get("tasks", [])
    return render(request, "core/person_detailview.html", {
        "person": data,
        "tasks": tasks,
        "status_liste": status_liste,
        "prio_liste": prio_liste
    })
