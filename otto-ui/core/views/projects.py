import requests
import json
from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from core.const import status_liste, prio_liste
import os
from dotenv import load_dotenv

load_dotenv()

OTTO_API_KEY = os.getenv("OTTO_API_KEY")
OTTO_API_URL = os.getenv("OTTO_API_URL")


def project_listview(request):
    res = requests.get(f"{OTTO_API_URL}/projekte", headers={"x-api-key": OTTO_API_KEY})
    projekte = res.json() if res.status_code == 200 else []
    personen_res = requests.get(f"{OTTO_API_URL}/personen", headers={"x-api-key": OTTO_API_KEY})
    personen = personen_res.json() if personen_res.status_code == 200 else []

    q = request.GET.get("q", "").lower()
    if q:
        projekte = [p for p in projekte if q in p.get("name", "").lower() or q in p.get("status", "").lower()]

    return render(request, "core/project_listview.html", {
        "projekte": projekte,
        "status_liste": status_liste,
        "prio_liste": prio_liste,
        "personen": personen
    })


@csrf_exempt
def project_detailview(request, project_id):
    if request.method == "POST":
        payload = json.loads(request.body)
        res = requests.get(f"{OTTO_API_URL}/projekte/{project_id}", headers={"x-api-key": OTTO_API_KEY})
        if res.status_code != 200:
            return JsonResponse({"error": "Projekt nicht gefunden"}, status=404)
        projekt = res.json()

        for k, v in payload.items():
            projekt[k] = v
        if isinstance(projekt.get("bearbeiter"), list):
            projekt["bearbeiter"] = projekt["bearbeiter"][0] if projekt["bearbeiter"] else None

        update = requests.put(
            f"{OTTO_API_URL}/projekte/{project_id}",
            headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
            data=json.dumps(projekt)
        )
        return JsonResponse({"success": True}) if update.status_code == 200 else JsonResponse({"error": "Fehler beim Speichern"}, status=500)

    projekt_res = requests.get(f"{OTTO_API_URL}/projekte/{project_id}", headers={"x-api-key": OTTO_API_KEY})
    projekt = projekt_res.json() if projekt_res.status_code == 200 else {}
    dateien_res = requests.get(f"{OTTO_API_URL}/projekte/{projekt.get('short', '')}/dateien", headers={"x-api-key": OTTO_API_KEY})
    dateien = dateien_res.json() if dateien_res.status_code == 200 else []
    tasks_res = requests.get(f"{OTTO_API_URL}/project/{project_id}/tasks", headers={"x-api-key": OTTO_API_KEY})
    tasks = tasks_res.json() if tasks_res.status_code == 200 else []
    personen_res = requests.get(f"{OTTO_API_URL}/personen", headers={"x-api-key": OTTO_API_KEY})
    personen = personen_res.json() if personen_res.status_code == 200 else []

    return render(request, "core/project_detailview.html", {
        "projekt": projekt,
        "personen": personen,
        "tasks": tasks,
        "dateien": dateien,
        "status_liste": status_liste,
        "prio_liste": prio_liste
    })