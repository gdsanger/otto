import requests
import json
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from .helpers import login_required
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from core.const import prio_liste, status_liste, typ_liste
from .ai import improve_description
import os
from dotenv import load_dotenv
import logging
load_dotenv()
logger = logging.getLogger(__name__)
OTTO_API_KEY = os.getenv("OTTO_API_KEY")
OTTO_API_URL = os.getenv("OTTO_API_URL")


def ensure_html(text: str) -> str:
    """Return text as simple HTML.

    If the text already seems to contain HTML tags, it is returned unchanged.
    Otherwise line breaks are converted into ``<br>`` and paragraphs are wrapped
    in ``<p>`` tags so that existing plain text is displayed nicely when rendered
    with TinyMCE.
    """
    if not text:
        return ""
    if "<" in text:
        return text
    paragraphs = text.split("\n\n")
    return "".join("<p>" + p.replace("\n", "<br>") + "</p>" for p in paragraphs)


def load_person_lists():
    res = requests.get(f"{OTTO_API_URL}/personen", headers={"x-api-key": OTTO_API_KEY})
    personen = res.json() if res.status_code == 200 else []
    personen_sorted = sorted(personen, key=lambda p: p.get("name", ""))
    agenten_sorted = [p for p in personen_sorted if p.get("rolle") in ["agent", "admin"]]
    return personen_sorted, agenten_sorted


@login_required
def task_listview(request):
    res = requests.get(f"{OTTO_API_URL}/tasks", headers={"x-api-key": OTTO_API_KEY})
    tasks = res.json() if res.status_code == 200 else []
    q = request.GET.get("q", "").lower()
    project_id = request.GET.get("project_id")
    without_project = request.GET.get("without_project")
    without_project = True if without_project else False
    try:
        page = int(request.GET.get("page", 1))
    except ValueError:
        page = 1
    per_page = 20
    personen, agenten = load_person_lists()
    projekte_res = requests.get(f"{OTTO_API_URL}/projekte", headers={"x-api-key": OTTO_API_KEY})
    projekte = projekte_res.json() if projekte_res.status_code == 200 else []
    sprints_res = requests.get(f"{OTTO_API_URL}/sprints", headers={"x-api-key": OTTO_API_KEY})
    sprints = sprints_res.json() if sprints_res.status_code == 200 else []
    sprint_map = {s.get("id"): s.get("name") for s in sprints}

    offene_tasks = []
    for t in tasks:
        if t.get("status", "").lower() != "✅ abgeschlossen":
            if q and q not in t.get("betreff", "").lower() and q not in t.get("beschreibung", "").lower():
                continue
            if project_id:
                if t.get("project_id") != project_id:
                    continue
            elif without_project:
                if t.get("project_id"):
                    continue
            termin_str = t.get("termin")
            try:
                termin_dt = datetime.fromisoformat(termin_str) if termin_str else None
            except ValueError:
                termin_dt = None
            t["termin_dt"] = termin_dt
            t["sprint_name"] = sprint_map.get(t.get("sprint_id"))
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
        "agenten": agenten,
        "projekte": projekte,
        "page": page,
        "total_pages": total_pages,
        "page_numbers": page_numbers,
        "selected_project": project_id,
        "without_project": without_project,
    })


@login_required
def task_archive_listview(request):
    res = requests.get(f"{OTTO_API_URL}/tasks", headers={"x-api-key": OTTO_API_KEY})
    tasks = res.json() if res.status_code == 200 else []
    q = request.GET.get("q", "").lower()
    project_id = request.GET.get("project_id")
    without_project = request.GET.get("without_project")
    without_project = True if without_project else False
    try:
        page = int(request.GET.get("page", 1))
    except ValueError:
        page = 1
    per_page = 20
    personen, agenten = load_person_lists()
    projekte_res = requests.get(f"{OTTO_API_URL}/projekte", headers={"x-api-key": OTTO_API_KEY})
    projekte = projekte_res.json() if projekte_res.status_code == 200 else []

    erledigte_tasks = []
    for t in tasks:
        if t.get("status", "").lower() == "✅ abgeschlossen":
            if q and q not in t.get("betreff", "").lower() and q not in t.get("beschreibung", "").lower():
                continue
            if project_id:
                if t.get("project_id") != project_id:
                    continue
            elif without_project:
                if t.get("project_id"):
                    continue
            termin_str = t.get("termin")
            try:
                termin_dt = datetime.fromisoformat(termin_str) if termin_str else None
            except ValueError:
                termin_dt = None
            t["termin_dt"] = termin_dt
            t["sprint_name"] = sprint_map.get(t.get("sprint_id"))
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
        "agenten": agenten,
        "projekte": projekte,
        "page": page,
        "total_pages": total_pages,
        "page_numbers": page_numbers,
        "selected_project": project_id,
        "without_project": without_project,
    })


@login_required
def task_kanban_view(request):
    res = requests.get(f"{OTTO_API_URL}/tasks", headers={"x-api-key": OTTO_API_KEY})
    tasks = res.json() if res.status_code == 200 else []

    personen, agenten = load_person_lists()
    personen_map = {p.get("id"): p.get("name") for p in personen}

    projekte_res = requests.get(f"{OTTO_API_URL}/projekte", headers={"x-api-key": OTTO_API_KEY})
    projekte = projekte_res.json() if projekte_res.status_code == 200 else []
    projekt_map = {p.get("id"): p.get("name") for p in projekte}
    sprints_res = requests.get(f"{OTTO_API_URL}/sprints", headers={"x-api-key": OTTO_API_KEY})
    sprints = sprints_res.json() if sprints_res.status_code == 200 else []
    sprint_map = {s.get("id"): s.get("name") for s in sprints}

    kanban_statuses = [s for s in status_liste if s not in ("✅ abgeschlossen", "📦 laufend")]
    grouped = {status: [] for status in kanban_statuses}
    for t in tasks:
        status = t.get("status") or status_liste[0]
        if status in ("✅ abgeschlossen", "📦 laufend"):
            continue
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
        t["sprint_name"] = sprint_map.get(t.get("sprint_id"))
        pid = t.get("project_id")
        t["project_name"] = projekt_map.get(pid, "") if pid else ""
        grouped[status].append(t)

    for lst in grouped.values():
        lst.sort(key=lambda x: x["termin_dt"] or datetime.max)

    grouped_list = [(status, grouped.get(status, [])) for status in kanban_statuses]

    context = {
        "grouped_list": grouped_list,
        "status_liste": kanban_statuses,
        "agenten": agenten,
        "projekte": projekte,
        "sprints": sprints,
    }
    return render(request, "core/task_kanban.html", context)


@login_required
@csrf_exempt
def task_create(request):
    logger.info("Task create called")
    logger.info(f"Request method: {request.body}")    
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            payload["beschreibung"] = ensure_html(payload.get("beschreibung", ""))
            payload["umsetzung"] = ensure_html(payload.get("umsetzung", ""))
            logger.info(f"Payload: {payload}")
            res = requests.post(
                f"{OTTO_API_URL}/tasks",
                headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
                data=json.dumps(payload),
            )
            if res.status_code in (200, 201):
                data = res.json()
                return JsonResponse({"success": True, "id": data.get("id")})
            logger.error(f"Error creating task: {res.status_code} - {res.text}")
            return JsonResponse({"error": "Fehler beim Speichern"}, status=500)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    task = {
        "betreff": request.GET.get("betreff", ""),
        "beschreibung": request.GET.get("beschreibung", ""),
        "status": request.GET.get("status", ""),
        "prio": request.GET.get("prio", ""),
        "project_id": request.GET.get("project_id", ""),
    }
   
    personen, agenten = load_person_lists()
    projekte_res = requests.get(f"{OTTO_API_URL}/projekte", headers={"x-api-key": OTTO_API_KEY})
    projekte = projekte_res.json() if projekte_res.status_code == 200 else []
    sprints_res = requests.get(f"{OTTO_API_URL}/sprints", headers={"x-api-key": OTTO_API_KEY})
    sprints = sprints_res.json() if sprints_res.status_code == 200 else []
    meetings_res = requests.get(f"{OTTO_API_URL}/meetings", headers={"x-api-key": OTTO_API_KEY})
    meetings = meetings_res.json() if meetings_res.status_code == 200 else []

    return render(request, "core/task_detailpage.html", {
        "task": task,
        "personen": personen,
        "agenten": agenten,
        "projekte": projekte,
        "prio_liste": prio_liste,
        "status_liste": status_liste,
        "typ_liste": typ_liste,
        "sprints": sprints,
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
def task_week_view(request):
    from datetime import date, timedelta
    week_str = request.GET.get("week")
    show_weekend = request.GET.get("weekend") == "1"
    today = date.today()
    if week_str:
        try:
            start = datetime.strptime(week_str + "-1", "%G-W%V-%u").date()
        except ValueError:
            start = today - timedelta(days=today.weekday())
    else:
        start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)

    res = requests.get(f"{OTTO_API_URL}/tasks", headers={"x-api-key": OTTO_API_KEY})
    tasks = res.json() if res.status_code == 200 else []

    # Projekte laden, um Namen zuordnen zu können
    projekte_res = requests.get(f"{OTTO_API_URL}/projekte", headers={"x-api-key": OTTO_API_KEY})
    projekte = projekte_res.json() if projekte_res.status_code == 200 else []
    projekt_map = {p.get("id"): p.get("name") for p in projekte}

    personen, agenten = load_person_lists()

    days = []
    weekday_abbr = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    for i in range(7):
        d = start + timedelta(days=i)
        if i < 5 or show_weekend:
            label = f"{weekday_abbr[d.weekday()]} {d.strftime('%d.%m')}"
            days.append({"iso": d.isoformat(), "label": label})

    board = []
    for p in agenten:
        per_tasks = {day["iso"]: [] for day in days}
        total_count = 0
        for t in tasks:
            if t.get("person_id") != p.get("id"):
                continue
            if t.get("status", "").lower() == "✅ abgeschlossen":
                continue
            termin = t.get("termin")
            try:
                termin_dt = datetime.fromisoformat(termin) if termin else None
            except ValueError:
                termin_dt = None
            if not termin_dt:
                continue
            if termin_dt.date() <= end:
                disp = termin_dt.date()
                if disp < start:
                    disp = start
                key = disp.isoformat()
                if key in per_tasks:
                    t["termin_formatiert"] = termin_dt.strftime("%d.%m.%Y")
                    pid = t.get("project_id")
                    t["project_name"] = projekt_map.get(pid, "") if pid else ""
                    per_tasks[key].append(t)
                    total_count += 1
        if any(per_tasks[d["iso"]] for d in days):
            board.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "tasks": per_tasks,
                "count": total_count,
            })

    prev_week = (start - timedelta(days=7)).strftime("%G-W%V")
    next_week = (start + timedelta(days=7)).strftime("%G-W%V")

    context = {
        "board": board,
        "days": days,
        "prev_week": prev_week,
        "next_week": next_week,
        "week_label": start.strftime("%d.%m") + " - " + end.strftime("%d.%m.%Y"),
        "show_weekend": show_weekend,
    }
    return render(request, "core/task_weekboard.html", context)

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
        task["beschreibung"] = ensure_html(request.POST.get("beschreibung"))
        task["umsetzung"] = ensure_html(request.POST.get("umsetzung"))
        task["tasktype"] = request.POST.get("tasktype")
        task["status"] = request.POST.get("status")
        task["prio"] = request.POST.get("prio")
        task["typ"] = request.POST.get("typ")
        task["person_id"] = request.POST.get("person_id")
        task["requester_id"] = request.POST.get("requester_id")
        task["project_id"] = request.POST.get("project_id") or None
        task["sprint_id"] = request.POST.get("sprint_id") or None
        task["erledigt"] = request.POST.get("erledigt") or None
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
            res = requests.get(
                f"{OTTO_API_URL}/tasks/{task_id}",
                headers={"x-api-key": OTTO_API_KEY}
            )
            if res.status_code != 200:
                return JsonResponse({"error": "Task nicht gefunden"}, status=404)
            task = res.json()
            for key, value in payload.items():
                if key == "aufwand":
                    value = int(value) if str(value).isdigit() else 0
                elif key == "tid":
                    if str(value).isdigit():
                        value = int(value)
                    else:
                        continue
                elif key in ["termin", "erledigt"] and value == "":
                    value = None
                elif key in ["beschreibung", "umsetzung"]:
                    value = ensure_html(value)
                task[key] = value
            update = requests.put(
                f"{OTTO_API_URL}/tasks/{task_id}",
                headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
                data=json.dumps(task)
            )
            return (
                JsonResponse({"success": True})
                if update.status_code == 200
                else JsonResponse({"error": "Fehler beim Speichern"}, status=500)
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    task_res = requests.get(f"{OTTO_API_URL}/tasks/{task_id}", headers={"x-api-key": OTTO_API_KEY})
    task = task_res.json()
    personen, agenten = load_person_lists()
    projekte_res = requests.get(f"{OTTO_API_URL}/projekte", headers={"x-api-key": OTTO_API_KEY})
    projekte = projekte_res.json() if projekte_res.status_code == 200 else []
    sprints_res = requests.get(f"{OTTO_API_URL}/sprints", headers={"x-api-key": OTTO_API_KEY})
    sprints = sprints_res.json() if sprints_res.status_code == 200 else []
    meetings_res = requests.get(f"{OTTO_API_URL}/meetings", headers={"x-api-key": OTTO_API_KEY})
    meetings = meetings_res.json() if meetings_res.status_code == 200 else []
    return render(request, "core/task_detailpage.html", {
        "task": task,
        "personen": personen,
        "agenten": agenten,
        "projekte": projekte,
        "meetings": meetings,
        "prio_liste": prio_liste,
        "status_liste": status_liste,
        "typ_liste": typ_liste,
        "sprints": sprints,
    })

@login_required
@csrf_exempt
def task_pageview(request, task_id):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            print("Received payload:", payload)
            res = requests.get(f"{OTTO_API_URL}/tasks/{task_id}", headers={"x-api-key": OTTO_API_KEY})
            if res.status_code != 200:
                return JsonResponse({"error": "Task nicht gefunden"}, status=404)
            task = res.json()
            for key, value in payload.items():
                if key == "aufwand":
                    value = int(value) if str(value).isdigit() else 0
                elif key == "tid":
                    if str(value).isdigit():
                        value = int(value)
                    else:
                        continue
                elif key in ["termin", "erledigt"] and value == "":
                    value = None
                elif key in ["beschreibung", "umsetzung"]:
                    value = ensure_html(value)
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
    task["id"] = task_id
    personen, agenten = load_person_lists()
    projekte_res = requests.get(f"{OTTO_API_URL}/projekte", headers={"x-api-key": OTTO_API_KEY})
    projekte = projekte_res.json() if projekte_res.status_code == 200 else []
    sprints_res = requests.get(f"{OTTO_API_URL}/sprints", headers={"x-api-key": OTTO_API_KEY})
    sprints = sprints_res.json() if sprints_res.status_code == 200 else []
    meetings_res = requests.get(f"{OTTO_API_URL}/meetings", headers={"x-api-key": OTTO_API_KEY})
    meetings = meetings_res.json() if meetings_res.status_code == 200 else []
    templates_dir = os.path.join(os.path.dirname(__file__), '../templates/emails/task')
    email_templates = [f[:-5] for f in os.listdir(templates_dir) if f.endswith('.html')]
    context_res = requests.get(
        f"{OTTO_API_URL}/context/aufgabe/{task_id}",
        headers={"x-api-key": OTTO_API_KEY},
    )
    task_context = context_res.json() if context_res.status_code == 200 else {}
    context_text = task_context
    similar_res = requests.get(
        f"{OTTO_API_URL}/tasks/{task_id}/similar",
        headers={"x-api-key": OTTO_API_KEY},
    )
    similar_tasks = similar_res.json() if similar_res.status_code == 200 else []
    comments_res = requests.get(
        f"{OTTO_API_URL}/tasks/{task_id}/comments",
        headers={"x-api-key": OTTO_API_KEY},
    )
    comments = comments_res.json() if comments_res.status_code == 200 else []
    personen_map = {p.get("id"): p.get("name") for p in personen}
    return render(request, "core/task_detailpage.html", {
        "task": task,
        "personen": personen,
        "agenten": agenten,
        "projekte": projekte,
        "meetings": meetings,
        "prio_liste": prio_liste,
        "status_liste": status_liste,
        "typ_liste": typ_liste,
        "sprints": sprints,
        "similar_tasks": similar_tasks,
        "comments": comments,
        "personen_map": personen_map,
        "context_json": json.dumps(task_context),
        "context_text": context_text,
        "email_templates": email_templates,
    })


@login_required
@csrf_exempt
def add_task_comment(request):
    if request.method == "POST":
        task_id = request.POST.get("task_id")
        text = request.POST.get("text", "").strip()
        send_email = request.POST.get("send_email") == "1"
        user = request.session.get("user", {})
        user_id = user.get("id")

        if not task_id or not text:
            return JsonResponse({"error": "Ungültige Daten."}, status=400)

        payload = {
            "datum": datetime.utcnow().isoformat(),
            "task_id": task_id,
            "user_id": user_id,
            "text": text,
            "type": "note",
        }

        res = requests.post(
            f"{OTTO_API_URL}/tasks/{task_id}/comments?send_email={'true' if send_email else 'false'}",
            headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
            data=json.dumps(payload),
        )

        if res.status_code in (200, 201):
            person_name = user.get("name", "")
            html = render_to_string(
                "components/comment_item.html",
                {"c": payload, "person_name": person_name},
            )
            return JsonResponse({"success": True, "html": html})

        try:
            error_detail = res.json().get("detail")
        except Exception:
            error_detail = None
        return JsonResponse(
            {"error": error_detail or "Fehler beim Speichern."},
            status=res.status_code or 500,
        )


    return JsonResponse({"error": "Ungültige Methode."}, status=405)


@login_required
@csrf_exempt
def improve_task_description(request):
    return improve_description(request)
