import requests
import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
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
    for ressource in team.get("ressourcen", []):
        anteil = ressource.get("anteil")
        if isinstance(anteil, str):
            ressource["anteil"] = anteil.replace(",", ".")
    personen_res = requests.get(f"{OTTO_API_URL}/personen", headers={"x-api-key": OTTO_API_KEY})
    personen = personen_res.json() if personen_res.status_code == 200 else []
    return render(request, "core/team_detailview.html", {"team": team, "personen": personen})


@login_required
@csrf_exempt
def team_create(request):
    if request.method != "POST":
        return JsonResponse({"error": "Ungültige Methode."}, status=405)

    name = request.POST.get("name")
    if not name:
        try:
            payload = json.loads(request.body or "{}")
            name = payload.get("name")
        except Exception:
            name = None

    if not name:
        return JsonResponse({"error": "Name fehlt."}, status=400)

    try:
        res = requests.post(
            f"{OTTO_API_URL}/teams",
            headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
            data=json.dumps({"teams": [{"name": name, "ressourcen": []}]})
        )
        if res.status_code not in (200, 201):
            return JsonResponse({"error": "Fehler beim Speichern"}, status=res.status_code)
        inserted_id = res.json().get("inserted_ids", [None])[0]
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    if request.headers.get("HX-Request") == "true":
        html = f'<tr><td><a href="/team/{inserted_id}/">{name}</a></td></tr>'
        return HttpResponse(html)

    return JsonResponse({"id": inserted_id}, status=201)
