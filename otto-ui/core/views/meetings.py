import requests
import json
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from .helpers import login_required
from django.views.decorators.csrf import csrf_exempt
from core.const import mandanten_liste, prio_liste, status_liste
import os
from dotenv import load_dotenv

load_dotenv()

OTTO_API_KEY = os.getenv("OTTO_API_KEY")
OTTO_API_URL = os.getenv("OTTO_API_URL")


@login_required
def meeting_listview(request):
    res = requests.get(f"{OTTO_API_URL}/meetings", headers={"x-api-key": OTTO_API_KEY})
    meetings = res.json() if res.status_code == 200 else []
    q = request.GET.get("q", "").lower()
    filtered = []
    for m in meetings:
        if q and q not in m.get("name", "").lower():
            continue
        try:
            m["_datum"] = datetime.fromisoformat(m["datum"])
        except:
            m["_datum"] = datetime.min
        filtered.append(m)
    filtered.sort(key=lambda m: m["_datum"], reverse=True)
    return render(request, "core/meeting_listview.html", {"meetings": filtered})


@login_required
@csrf_exempt
def meeting_detailview(request, meeting_id):
    meeting_res = requests.get(f"{OTTO_API_URL}/meetings/{meeting_id}", headers={"x-api-key": OTTO_API_KEY})
    if meeting_res.status_code != 200:
        return HttpResponse("Meeting nicht gefunden", status=404)
    meeting = meeting_res.json()
    personen_res = requests.get(f"{OTTO_API_URL}/personen", headers={"x-api-key": OTTO_API_KEY})
    personen = personen_res.json() if personen_res.status_code == 200 else []

    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            data = {
                "id": meeting_id,
                "name": payload.get("name"),
                "beschreibung": payload.get("beschreibung"),
                "datum": payload.get("datum"),
                "von": payload.get("von"),
                "bis": payload.get("bis"),
                "mandant": payload.get("mandant"),
                "teilnehmer": payload.get("personen_ids", []),
                "themen": payload.get("themen"),
            }
            update = requests.put(
                f"{OTTO_API_URL}/meetings/{meeting_id}",
                headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
                data=json.dumps(data)
            )
            if update.status_code == 200:
                return JsonResponse({"success": True})
            return JsonResponse({"error": "Fehler beim Speichern."}, status=500)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    tasks_res = requests.get(f"{OTTO_API_URL}/meeting/{meeting_id}/tasks", headers={"x-api-key": OTTO_API_KEY})
    tasks = tasks_res.json() if tasks_res.status_code == 200 else []
    meeting["tasks"] = tasks

    return render(request, "core/meeting_detailview.html", {
        "meeting": meeting,
        "personen": personen,
        "mandanten": mandanten_liste,
        "status_liste": status_liste,
        "prio_liste": prio_liste
    })