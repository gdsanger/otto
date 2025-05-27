import os
import requests
import json
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .helpers import login_required
from core.const import sprint_typ, sprint_status
from dotenv import load_dotenv

load_dotenv()

OTTO_API_KEY = os.getenv("OTTO_API_KEY")
OTTO_API_URL = os.getenv("OTTO_API_URL")


@login_required
def sprint_listview(request):
    res = requests.get(f"{OTTO_API_URL}/sprints", headers={"x-api-key": OTTO_API_KEY})
    sprints = res.json() if res.status_code == 200 else []
    q = request.GET.get("q", "").lower()
    if q:
        sprints = [s for s in sprints if q in s.get("name", "").lower()]
    return render(request, "core/sprint_listview.html", {"sprints": sprints, "sprint_status": sprint_status})


@login_required
@csrf_exempt
def sprint_detailview(request, sprint_id):
    if request.method == "POST":
        payload = json.loads(request.body)
        res = requests.get(f"{OTTO_API_URL}/sprints/{sprint_id}", headers={"x-api-key": OTTO_API_KEY})
        if res.status_code != 200:
            return JsonResponse({"error": "Sprint nicht gefunden"}, status=404)
        sprint = res.json()
        for k, v in payload.items():
            sprint[k] = v
        update = requests.put(
            f"{OTTO_API_URL}/sprints/{sprint_id}",
            headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
            data=json.dumps(sprint),
        )
        return JsonResponse({"success": True}) if update.status_code == 200 else JsonResponse({"error": "Fehler beim Speichern"}, status=500)

    sprint_res = requests.get(f"{OTTO_API_URL}/sprints/{sprint_id}", headers={"x-api-key": OTTO_API_KEY})
    sprint = sprint_res.json() if sprint_res.status_code == 200 else {}
    projekte_res = requests.get(f"{OTTO_API_URL}/projekte", headers={"x-api-key": OTTO_API_KEY})
    projekte = projekte_res.json() if projekte_res.status_code == 200 else []
    return render(request, "core/sprint_detailview.html", {
        "sprint": sprint,
        "projekte": projekte,
        "sprint_typ": sprint_typ,
        "sprint_status": sprint_status,
    })


@login_required
@csrf_exempt
def sprint_create(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            res = requests.post(
                f"{OTTO_API_URL}/sprints",
                headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
                data=json.dumps(payload),
            )
            if res.status_code in (200, 201):
                data = res.json()
                return JsonResponse({"success": True, "id": data.get("id")})
            return JsonResponse({"error": "Fehler beim Speichern"}, status=500)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    projekte_res = requests.get(f"{OTTO_API_URL}/projekte", headers={"x-api-key": OTTO_API_KEY})
    projekte = projekte_res.json() if projekte_res.status_code == 200 else []
    return render(request, "core/sprint_detailview.html", {
        "sprint": {},
        "projekte": projekte,
        "sprint_typ": sprint_typ,
        "sprint_status": sprint_status,
    })


@login_required
@csrf_exempt
def delete_sprint(request):
    if request.method == "POST":
        sprint_id = request.POST.get("sprint_id")
        if not sprint_id:
            return JsonResponse({"error": "Keine Sprint-ID."}, status=400)
        res = requests.delete(f"{OTTO_API_URL}/sprints/{sprint_id}", headers={"x-api-key": OTTO_API_KEY})
        if res.status_code == 200:
            if request.headers.get("HX-Request") == "true":
                return HttpResponse("")
            return redirect("/sprint/")
        return JsonResponse({"error": "Fehler beim L\u00f6schen."}, status=500)
    return JsonResponse({"error": "Ung\u00fcltige Methode."}, status=405)
