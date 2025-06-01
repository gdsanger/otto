import os
import requests
import json
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .helpers import login_required
from core.const import sprint_typ, sprint_status, status_liste, typ_liste
from django.views.decorators.http import require_POST
from dotenv import load_dotenv

load_dotenv()

OTTO_API_KEY = os.getenv("OTTO_API_KEY")
OTTO_API_URL = os.getenv("OTTO_API_URL")


def load_person_lists():
    res = requests.get(f"{OTTO_API_URL}/personen", headers={"x-api-key": OTTO_API_KEY})
    personen = res.json() if res.status_code == 200 else []
    personen_sorted = sorted(personen, key=lambda p: p.get("name", ""))
    agenten_sorted = [p for p in personen_sorted if p.get("rolle") in ["agent", "admin"]]
    return personen_sorted, agenten_sorted


@login_required
def sprint_listview(request):
    res = requests.get(f"{OTTO_API_URL}/sprints", headers={"x-api-key": OTTO_API_KEY})
    sprints = res.json() if res.status_code == 200 else []

    projekte_res = requests.get(f"{OTTO_API_URL}/projekte", headers={"x-api-key": OTTO_API_KEY})
    projekte = projekte_res.json() if projekte_res.status_code == 200 else []
    projekt_map = {p.get("id"): p.get("name") for p in projekte}
    for s in sprints:
        s["projekt_name"] = projekt_map.get(s.get("projekt_id"), "")

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

    tasks_res = requests.get(
        f"{OTTO_API_URL}/sprint/{sprint_id}/tasks",
        headers={"x-api-key": OTTO_API_KEY},
    )
    tasks = tasks_res.json() if tasks_res.status_code == 200 else []

    task_q = request.GET.get("task_q", "").lower()
    try:
        task_page = int(request.GET.get("task_page", 1))
    except ValueError:
        task_page = 1
    task_per_page = 10

    filtered_tasks = []
    for t in tasks:
        if task_q:
            if task_q not in t.get("betreff", "").lower() and task_q not in t.get("beschreibung", "").lower():
                continue
        filtered_tasks.append(t)

    task_total_pages = max(1, (len(filtered_tasks) + task_per_page - 1) // task_per_page)
    if task_page < 1:
        task_page = 1
    if task_page > task_total_pages:
        task_page = task_total_pages
    start = (task_page - 1) * task_per_page
    end = start + task_per_page
    paginated_tasks = filtered_tasks[start:end]
    task_page_numbers = range(1, task_total_pages + 1)

    personen, agenten = load_person_lists()

    return render(request, "core/sprint_detailview.html", {
        "sprint": sprint,
        "projekte": projekte,
        "sprint_typ": sprint_typ,
        "sprint_status": sprint_status,
        "tasks": paginated_tasks,
        "personen": personen,
        "agenten": agenten,
        "status_liste": status_liste,
        "typ_liste": typ_liste,
        "task_page": task_page,
        "task_total_pages": task_total_pages,
        "task_page_numbers": task_page_numbers,
        "task_q": task_q,
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


@require_POST
@csrf_exempt
def sprint_create_task(request):
    """Create a new task directly from the sprint view."""
    data = json.loads(request.body)
    response = requests.post(
        f"{OTTO_API_URL}/tasks",
        headers={"x-api-key": OTTO_API_KEY},
        json={
            "betreff": data["betreff"],
            "beschreibung": "",
            "umsetzung": "",
            "zuständig": data.get("zuständig", "Otto"),
            "person_id": data.get("person_id"),
            "requester_id": data.get("requester_id"),
            "aufwand": 1,
            "prio": data.get("prio", "mittel"),
            "status": data.get("status", "Offen"),
            "termin": data.get("termin"),
            "project_id": data.get("project_id"),
            "sprint_id": data["sprint_id"],
        }
    )
    return JsonResponse(response.json(), status=response.status_code)
