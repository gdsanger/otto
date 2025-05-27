import requests
import json
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from .helpers import login_required
from django.views.decorators.csrf import csrf_exempt
from core.const import prio_liste, status_liste, typ_liste
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
    try:
        page = int(request.GET.get("page", 1))
    except ValueError:
        page = 1
    per_page = 20
    personen_res = requests.get(f"{OTTO_API_URL}/personen", headers={"x-api-key": OTTO_API_KEY})
    personen = personen_res.json() if personen_res.status_code == 200 else []

    offene_tasks = []
    for t in tasks:
        if t.get("status", "").lower() != "✅ abgeschlossen":
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

    total_pages = max(1, (len(offene_tasks) + per_page - 1) // per_page)
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages
    start = (page - 1) * per_page
    end = start + per_page
    paginated_tasks = offene_tasks[start:end]

    page_numbers = range(1, total_pages + 1)
    return render(request, "core/task_listview.html", {
        "tasks": paginated_tasks,
        "status_liste": status_liste,
        "typ_liste": typ_liste,
        "personen": personen,
        "page": page,
        "total_pages": total_pages,
        "page_numbers": page_numbers,
    })


@login_required
def task_archive_listview(request):
    res = requests.get(f"{OTTO_API_URL}/tasks", headers={"x-api-key": OTTO_API_KEY})
    tasks = res.json() if res.status_code == 200 else []
    q = request.GET.get("q", "").lower()
    try:
        page = int(request.GET.get("page", 1))
    except ValueError:
        page = 1
    per_page = 20
    personen_res = requests.get(f"{OTTO_API_URL}/personen", headers={"x-api-key": OTTO_API_KEY})
    personen = personen_res.json() if personen_res.status_code == 200 else []

    erledigte_tasks = []
    for t in tasks:
        if t.get("status", "").lower() == "✅ abgeschlossen":
            if q and q not in t.get("betreff", "").lower() and q not in t.get("beschreibung", "").lower():
                continue
            termin_str = t.get("termin")
            try:
                termin_dt = datetime.fromisoformat(termin_str) if termin_str else None
            except ValueError:
                termin_dt = None
            t["termin_dt"] = termin_dt
            erledigte_tasks.append(t)

    erledigte_tasks.sort(key=lambda x: x["termin_dt"] or datetime.max)
    for t in erledigte_tasks:
        t["termin_formatiert"] = t["termin_dt"].strftime("%d.%m.%Y") if t["termin_dt"] else "-"

    total_pages = max(1, (len(erledigte_tasks) + per_page - 1) // per_page)
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages
    start = (page - 1) * per_page
    end = start + per_page
    paginated_tasks = erledigte_tasks[start:end]

    page_numbers = range(1, total_pages + 1)
    return render(request, "core/task_archive_listview.html", {
        "tasks": paginated_tasks,
        "status_liste": status_liste,
        "typ_liste": typ_liste,
        "personen": personen,
        "page": page,
        "total_pages": total_pages,
        "page_numbers": page_numbers,
    })


@login_required
def task_kanban_view(request):
    res = requests.get(f"{OTTO_API_URL}/tasks", headers={"x-api-key": OTTO_API_KEY})
    tasks = res.json() if res.status_code == 200 else []

    personen_res = requests.get(f"{OTTO_API_URL}/personen", headers={"x-api-key": OTTO_API_KEY})
    personen = personen_res.json() if personen_res.status_code == 200 else []
    personen_map = {p.get("id"): p.get("name") for p in personen}
    agenten = [p for p in personen if p.get("rolle") in ["agent", "admin"]]

    grouped = {status: [] for status in status_liste}
    for t in tasks:
        status = t.get("status") or status_liste[0]
        if status not in grouped:
            grouped[status] = []
        termin = t.get("termin")
        try:
            termin_dt = datetime.fromisoformat(termin) if termin else None
        except ValueError:
            termin_dt = None
        t["termin_dt"] = termin_dt
        t["termin_formatiert"] = termin_dt.strftime("%d.%m.%Y") if termin_dt else "-"
        t["person_name"] = personen_map.get(t.get("person_id"), "-")
        grouped[status].append(t)

    for lst in grouped.values():
        lst.sort(key=lambda x: x["termin_dt"] or datetime.max)

    grouped_list = [(status, grouped.get(status, [])) for status in status_liste]

    context = {
        "grouped_list": grouped_list,
        "status_liste": status_liste,
        "agenten": agenten,
    }
    return render(request, "core/task_kanban.html", context)


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
        "typ_liste": typ_liste,
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
def update_task_type(request):
    if request.method == "POST":
        task_id = request.POST.get("task_id")
        print("task_id", task_id)
        new_tasktype = request.POST.get("tasktype")
        print("new_tasktype", new_tasktype)
        get_res = requests.get(f"{OTTO_API_URL}/tasks/{task_id}", headers={"x-api-key": OTTO_API_KEY})
        print("get_res", get_res.status_code, get_res.text)
        if get_res.status_code != 200:
            return JsonResponse({"error": "Task nicht gefunden."}, status=404)
        task = get_res.json()
        task["tasktype"] = new_tasktype
        update_res = requests.put(
            f"{OTTO_API_URL}/tasks/{task_id}",
            headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
            data=json.dumps(task)
        )
        if update_res.status_code == 200:
            return HttpResponse(task["tasktype"])
        else:
            return JsonResponse({"error": "Fehler beim Speichern."}, status=500)
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
def update_task_typ(request):
    if request.method == "POST":
        task_id = request.POST.get("task_id")
        new_typ = request.POST.get("typ")
        get_res = requests.get(f"{OTTO_API_URL}/tasks/{task_id}", headers={"x-api-key": OTTO_API_KEY})
        if get_res.status_code != 200:
            return JsonResponse({"error": "Task nicht gefunden."}, status=404)
        task = get_res.json()
        task["typ"] = new_typ
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
        task["tasktype"] = request.POST.get("tasktype")
        task["status"] = request.POST.get("status")
        task["prio"] = request.POST.get("prio")
        task["typ"] = request.POST.get("typ")
        task["person_id"] = request.POST.get("person_id")
        task["project_id"] = request.POST.get("project_id") or None
        task["meeting_id"] = request.POST.get("meeting_id") or None
        aufwand = request.POST.get("aufwand")
        task["aufwand"] = int(aufwand) if aufwand and aufwand.isdigit() else 0
        tid = request.POST.get("tid")
        if tid and tid.isdigit():
            task["tid"] = int(tid)
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
        "typ_liste": typ_liste,
    })

@login_required
@csrf_exempt
def task_pageview(request, task_id):
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
    return render(request, "core/task_detailpage.html", {
        "task": task,
        "personen": personen,
        "projekte": projekte,
        "meetings": meetings,
        "prio_liste": prio_liste,
        "status_liste": status_liste,
        "typ_liste": typ_liste,
    })
