import requests
import json
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from .helpers import login_required
from django.views.decorators.csrf import csrf_exempt
from core.const import prio_liste, status_liste
import os
from dotenv import load_dotenv

load_dotenv()

OTTO_API_KEY = os.getenv("OTTO_API_KEY")
OTTO_API_URL = os.getenv("OTTO_API_URL")


@login_required
def task_listview(request):
    res = requests.get(f"{OTTO_API_URL}/tasks", headers={"x-api-key": OTTO_API_KEY})
    tasks = res.json() if res.status_code == 200 else []
    q = request.GET.get("q", "").lower()
    personen_res = requests.get(f"{OTTO_API_URL}/personen", headers={"x-api-key": OTTO_API_KEY})
    personen = personen_res.json() if personen_res.status_code == 200 else []

    offene_tasks = []
    for t in tasks:
        if t.get("status", "").lower() != "abgeschlossen":
            if q and q not in t.get("betreff", "").lower() and q not in t.get("beschreibung", "").lower():
                continue
            termin_str = t.get("termin")
            try:
                termin_dt = datetime.fromisoformat(termin_str) if termin_str else None
            except ValueError:
                termin_dt = None
            t["termin_dt"] = termin_dt
            offene_tasks.append(t)

    offene_tasks.sort(key=lambda x: x["termin_dt"] or datetime.max)
    for t in offene_tasks:
        t["termin_formatiert"] = t["termin_dt"].strftime("%d.%m.%Y") if t["termin_dt"] else "-"

    status_liste = ["offen", "in Arbeit", "laufend", "wartet", "abgeschlossen"]
    return render(request, "core/task_listview.html", {
        "tasks": offene_tasks,
        "status_liste": status_liste,
        "personen": personen
    })


@login_required
@csrf_exempt
def task_create(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            res = requests.post(
                f"{OTTO_API_URL}/tasks",
                headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
                data=json.dumps(payload),
            )
            if res.status_code in (200, 201):
                data = res.json()
                return JsonResponse({"success": True, "id": data.get("id")})
            return JsonResponse({"error": "Fehler beim Speichern"}, status=500)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    task = {}
    if request.GET.get("project_id"):
        task["project_id"] = request.GET["project_id"]
    if request.GET.get("meeting_id"):
        task["meeting_id"] = request.GET["meeting_id"]

    personen_res = requests.get(f"{OTTO_API_URL}/personen", headers={"x-api-key": OTTO_API_KEY})
    personen = personen_res.json() if personen_res.status_code == 200 else []
    projekte_res = requests.get(f"{OTTO_API_URL}/projekte", headers={"x-api-key": OTTO_API_KEY})
    projekte = projekte_res.json() if projekte_res.status_code == 200 else []
    meetings_res = requests.get(f"{OTTO_API_URL}/meetings", headers={"x-api-key": OTTO_API_KEY})
    meetings = meetings_res.json() if meetings_res.status_code == 200 else []

    return render(request, "core/task_detailview.html", {
        "task": task,
        "personen": personen,
        "projekte": projekte,
        "meetings": meetings,
        "prio_liste": prio_liste,
        "status_liste": status_liste,
    })


@login_required
@csrf_exempt
def update_task_status(request):
    if request.method == "POST":
        task_id = request.POST.get("task_id")
        new_status = request.POST.get("status")
        get_res = requests.get(f"{OTTO_API_URL}/tasks/{task_id}", headers={"x-api-key": OTTO_API_KEY})
        if get_res.status_code != 200:
            return JsonResponse({"error": "Task nicht gefunden."}, status=404)
        task = get_res.json()
        task["status"] = new_status
        update_res = requests.put(
            f"{OTTO_API_URL}/tasks/{task_id}",
            headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
            data=json.dumps(task)
        )
        return HttpResponse("OK") if update_res.status_code == 200 else JsonResponse({"error": "Fehler beim Speichern."}, status=500)
    return JsonResponse({"error": "Ungültige Methode."}, status=405)


@login_required
@csrf_exempt
def update_task_person(request):
    if request.method == "POST":
        task_id = request.POST.get("task_id")
        new_person_id = request.POST.get("person_id")
        get_res = requests.get(f"{OTTO_API_URL}/tasks/{task_id}", headers={"x-api-key": OTTO_API_KEY})
        if get_res.status_code != 200:
            return JsonResponse({"error": "Task nicht gefunden."}, status=404)
        task = get_res.json()
        task["person_id"] = new_person_id
        update_res = requests.put(
            f"{OTTO_API_URL}/tasks/{task_id}",
            headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
            data=json.dumps(task)
        )
        return HttpResponse("OK") if update_res.status_code == 200 else JsonResponse({"error": "Fehler beim Speichern."}, status=500)
    return JsonResponse({"error": "Ungültige Methode."}, status=405)


@login_required
@csrf_exempt
def update_task_details(request):
    if request.method == "POST":
        task_id = request.POST.get("task_id")
        get_res = requests.get(f"{OTTO_API_URL}/tasks/{task_id}", headers={"x-api-key": OTTO_API_KEY})
        if get_res.status_code != 200:
            return JsonResponse({"error": "Task nicht gefunden."}, status=404)
        task = get_res.json()
        task["betreff"] = request.POST.get("betreff")
        task["beschreibung"] = request.POST.get("beschreibung")
        task["status"] = request.POST.get("status")
        task["prio"] = request.POST.get("prio")
        task["person_id"] = request.POST.get("person_id")
        task["project_id"] = request.POST.get("project_id") or None
        task["meeting_id"] = request.POST.get("meeting_id") or None
        aufwand = request.POST.get("aufwand")
        task["aufwand"] = int(aufwand) if aufwand and aufwand.isdigit() else 0
        update_res = requests.put(
            f"{OTTO_API_URL}/tasks/{task_id}",
            headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
            data=json.dumps(task)
        )
        return redirect("/task/?saved=1") if update_res.status_code == 200 else JsonResponse({"error": "Fehler beim Speichern."}, status=500)
    return JsonResponse({"error": "Ungültige Methode."}, status=405)


@login_required
@csrf_exempt
def delete_task(request):
    if request.method == "POST":
        task_id = request.POST.get("task_id")
        if not task_id:
            return JsonResponse({"error": "Keine Task-ID."}, status=400)
        res = requests.delete(f"{OTTO_API_URL}/tasks/{task_id}", headers={"x-api-key": OTTO_API_KEY})
        if res.status_code == 200:
            if request.headers.get("HX-Request") == "true":
                return HttpResponse("")
            return redirect("/task/?deleted=1")
        return JsonResponse({"error": "Fehler beim Löschen."}, status=500)
    return JsonResponse({"error": "Ungültige Methode."}, status=405)


@login_required
@csrf_exempt
def task_detail_or_update(request, task_id):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            res = requests.get(f"{OTTO_API_URL}/tasks/{task_id}", headers={"x-api-key": OTTO_API_KEY})
            if res.status_code != 200:
                return JsonResponse({"error": "Task nicht gefunden"}, status=404)
            task = res.json()
            for key, value in payload.items():
                task[key] = value
            update = requests.put(
                f"{OTTO_API_URL}/tasks/{task_id}",
                headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
                data=json.dumps(task)
            )
            return JsonResponse({"success": True}) if update.status_code == 200 else JsonResponse({"error": "Fehler beim Speichern"}, status=500)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    task_res = requests.get(f"{OTTO_API_URL}/tasks/{task_id}", headers={"x-api-key": OTTO_API_KEY})
    task = task_res.json()
    personen_res = requests.get(f"{OTTO_API_URL}/personen", headers={"x-api-key": OTTO_API_KEY})
    personen = personen_res.json() if personen_res.status_code == 200 else []
    projekte_res = requests.get(f"{OTTO_API_URL}/projekte", headers={"x-api-key": OTTO_API_KEY})
    projekte = projekte_res.json() if projekte_res.status_code == 200 else []
    meetings_res = requests.get(f"{OTTO_API_URL}/meetings", headers={"x-api-key": OTTO_API_KEY})
    meetings = meetings_res.json() if meetings_res.status_code == 200 else []
    return render(request, "core/task_detailview.html", {
        "task": task,
        "personen": personen,
        "projekte": projekte,
        "meetings": meetings,
        "prio_liste": prio_liste,
        "status_liste": status_liste,
    })
