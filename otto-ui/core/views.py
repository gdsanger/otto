import requests
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from core.const import status_liste, mandanten_liste, prio_liste

load_dotenv()  # Lädt .env aus dem Projektverzeichnis

OTTO_API_KEY = os.getenv("OTTO_API_KEY")
OTTO_API_URL = os.getenv("OTTO_API_URL")



def home(request):
    return render(request, "core/home.html")

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
        if t["termin_dt"]:
            t["termin_formatiert"] = t["termin_dt"].strftime("%d.%m.%Y")
        else:
            t["termin_formatiert"] = "-"

    status_liste = ["offen", "in Arbeit", "laufend", "wartet", "abgeschlossen"]
    return render(request, "core/task_listview.html", {
        "tasks": offene_tasks,
        "status_liste": status_liste,
        "personen": personen
    })

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

        if update_res.status_code == 200:
            return HttpResponse("OK")
        else:
            return JsonResponse({"error": "Fehler beim Speichern."}, status=500)

    return JsonResponse({"error": "Ungültige Methode."}, status=405)

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

        if update_res.status_code == 200:
            return HttpResponse("OK")
        else:
            return JsonResponse({"error": "Fehler beim Speichern."}, status=500)

    return JsonResponse({"error": "Ungültige Methode."}, status=405)

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

        if update_res.status_code == 200:
            return redirect("/task/?saved=1")
        else:
            return JsonResponse({"error": "Fehler beim Speichern."}, status=500)

    return JsonResponse({"error": "Ungültige Methode."}, status=405)

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
            if update.status_code == 200:
                return JsonResponse({"success": True})
            return JsonResponse({"error": "Fehler beim Speichern"}, status=500)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    else:  # GET
        task_res = requests.get(f"{OTTO_API_URL}/tasks/{task_id}", headers={"x-api-key": OTTO_API_KEY})
        task = task_res.json()

        personen_res = requests.get(f"{OTTO_API_URL}/personen", headers={"x-api-key": OTTO_API_KEY})
        personen = personen_res.json() if personen_res.status_code == 200 else []

        return render(request, "core/task_detailview.html", {
            "task": task,
            "personen": personen,
        })


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
        "mandanten": mandanten_liste
    })

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
        else:
            return JsonResponse({"error": "Fehler beim Löschen."}, status=500)
    return JsonResponse({"error": "Ungültige Methode."}, status=405)

@csrf_exempt
def project_detailview(request, project_id):
   
    if request.method == "POST":
        payload = json.loads(request.body)
      
        # Projekt holen
        res = requests.get(f"{OTTO_API_URL}/projekte/{project_id}", headers={"x-api-key": OTTO_API_KEY})
        if res.status_code != 200:
            return JsonResponse({"error": "Projekt nicht gefunden"}, status=404)
        projekt = res.json()

        # Einzelne Felder überschreiben
        for k, v in payload.items():
            projekt[k] = v
        if isinstance(projekt.get("bearbeiter"), list):
            projekt["bearbeiter"] = projekt["bearbeiter"][0] if projekt["bearbeiter"] else None
        print(projekt)

        update = requests.put(
            f"{OTTO_API_URL}/projekte/{project_id}",
            headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
            data=json.dumps(projekt)
        )
        if update.status_code == 200:
            return JsonResponse({"success": True})
        return JsonResponse({"error": "Fehler beim Speichern"}, status=500)

    # GET – Detailansicht rendern
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


def parse_termin(t):
    try:
        return datetime.fromisoformat(t["termin"]) if t["termin"] else datetime.max
    except:
        return datetime.max

