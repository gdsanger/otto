import requests
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .helpers import login_required
import os
from dotenv import load_dotenv

load_dotenv()

OTTO_API_KEY = os.getenv("OTTO_API_KEY")
OTTO_API_URL = os.getenv("OTTO_API_URL")

@login_required
def team_listview(request):
    res = requests.get(f"{OTTO_API_URL}/teams", headers={"x-api-key": OTTO_API_KEY})
    teams = res.json() if res.status_code == 200 else []
    q = request.GET.get("q", "").lower()
    if q:
        teams = [t for t in teams if q in t.get("name", "").lower()]
    return render(request, "core/team_listview.html", {"teams": teams})

@login_required
@csrf_exempt
def team_detailview(request, team_id):
    if request.method == "POST":
        payload = json.loads(request.body)
        res = requests.get(f"{OTTO_API_URL}/teams/{team_id}", headers={"x-api-key": OTTO_API_KEY})
        if res.status_code != 200:
            return JsonResponse({"error": "Team nicht gefunden"}, status=404)
        team = res.json()
        for k, v in payload.items():
            team[k] = v
        update = requests.put(
            f"{OTTO_API_URL}/teams/{team_id}",
            headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
            data=json.dumps(team)
        )
        return JsonResponse({"success": True}) if update.status_code == 200 else JsonResponse({"error": "Fehler beim Speichern"}, status=500)

    res = requests.get(f"{OTTO_API_URL}/teams/{team_id}", headers={"x-api-key": OTTO_API_KEY})
    if res.status_code != 200:
        return render(request, "core/team_detailview.html", {"team": {}, "personen": []})
    team = res.json()
    personen_res = requests.get(f"{OTTO_API_URL}/personen", headers={"x-api-key": OTTO_API_KEY})
    personen = personen_res.json() if personen_res.status_code == 200 else []
    return render(request, "core/team_detailview.html", {"team": team, "personen": personen})
