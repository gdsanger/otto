import requests
import json
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from .helpers import login_required
from django.views.decorators.csrf import csrf_exempt
from core.const import status_liste, prio_liste, projekt_typ, typ_liste
import os
from dotenv import load_dotenv
from django.views.decorators.http import require_POST

load_dotenv()

OTTO_API_KEY = os.getenv("OTTO_API_KEY")
OTTO_API_URL = os.getenv("OTTO_API_URL")


def load_person_lists():
    res = requests.get(f"{OTTO_API_URL}/personen", headers={"x-api-key": OTTO_API_KEY})
    personen = res.json() if res.status_code == 200 else []
    personen_sorted = sorted(personen, key=lambda p: p.get("name", ""))
    agenten_sorted = [
        p for p in personen_sorted if p.get("rolle") in ["agent", "admin"]
    ]
    return personen_sorted, agenten_sorted


@login_required
def project_listview(request):
    res = requests.get(f"{OTTO_API_URL}/projekte", headers={"x-api-key": OTTO_API_KEY})
    projekte = res.json() if res.status_code == 200 else []
    personen, agenten = load_person_lists()

    q = request.GET.get("q", "").lower()
    if q:
        projekte = [
            p
            for p in projekte
            if q in p.get("name", "").lower() or q in p.get("status", "").lower()
        ]

    return render(
        request,
        "core/project_listview.html",
        {
            "projekte": projekte,
            "status_liste": status_liste,
            "prio_liste": prio_liste,
            "projekt_typ": projekt_typ,
            "personen": personen,
            "agenten": agenten,
        },
    )


@login_required
@csrf_exempt
def project_create(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            payload.setdefault("klassifikation", "Projekt")
            res = requests.post(
                f"{OTTO_API_URL}/projekte",
                headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
                data=json.dumps({"projekte": [payload]}),
            )
            if res.status_code in (200, 201):
                inserted_id = res.json().get("inserted_ids", [None])[0]
                return JsonResponse({"success": True, "id": inserted_id})
            return JsonResponse({"error": "Fehler beim Speichern"}, status=500)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    personen, agenten = load_person_lists()
    return render(
        request,
        "core/project_detailview.html",
        {
            "projekt": {},
            "personen": personen,
            "agenten": agenten,
            "tasks": [],
            "messages": [],
            "dateien": [],
            "status_liste": status_liste,
            "prio_liste": prio_liste,
            "typ_liste": typ_liste,
        },
    )


@login_required
@csrf_exempt
def project_detailview(request, project_id):
    if request.method == "POST":
        payload = json.loads(request.body)
        res = requests.get(
            f"{OTTO_API_URL}/projekte/{project_id}", headers={"x-api-key": OTTO_API_KEY}
        )
        if res.status_code != 200:
            return JsonResponse({"error": "Projekt nicht gefunden"}, status=404)
        projekt = res.json()

        for k, v in payload.items():
            projekt[k] = v
        if isinstance(projekt.get("bearbeiter"), list):
            projekt["bearbeiter"] = (
                projekt["bearbeiter"][0] if projekt["bearbeiter"] else None
            )

        update = requests.put(
            f"{OTTO_API_URL}/projekte/{project_id}",
            headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
            data=json.dumps(projekt),
        )
        return (
            JsonResponse({"success": True})
            if update.status_code == 200
            else JsonResponse({"error": "Fehler beim Speichern"}, status=500)
        )

    projekt_res = requests.get(
        f"{OTTO_API_URL}/projekte/{project_id}", headers={"x-api-key": OTTO_API_KEY}
    )
    projekt = projekt_res.json() if projekt_res.status_code == 200 else {}
    dateien_res = requests.get(
        f"{OTTO_API_URL}/sharepoint/projekte/{projekt.get('short', '')}/dateien",
        headers={"x-api-key": OTTO_API_KEY},
    )
    dateien = dateien_res.json() if dateien_res.status_code == 200 else []

    tasks_res = requests.get(
        f"{OTTO_API_URL}/project/{project_id}/tasks",
        headers={"x-api-key": OTTO_API_KEY},
    )
    tasks = tasks_res.json() if tasks_res.status_code == 200 else []

    task_q = request.GET.get("task_q", "").lower()
    sprint_id_filter = request.GET.get("sprint_id")
    try:
        task_page = int(request.GET.get("task_page", 1))
    except ValueError:
        task_page = 1
    task_per_page = 10

    filtered_tasks = []
    for t in tasks:
        if task_q:
            if (
                task_q not in t.get("betreff", "").lower()
                and task_q not in t.get("beschreibung", "").lower()
            ):
                continue
        if sprint_id_filter and str(t.get("sprint_id")) != sprint_id_filter:
            continue
        filtered_tasks.append(t)

    task_total_pages = max(
        1, (len(filtered_tasks) + task_per_page - 1) // task_per_page
    )
    if task_page < 1:
        task_page = 1
    if task_page > task_total_pages:
        task_page = task_total_pages
    start = (task_page - 1) * task_per_page
    end = start + task_per_page
    paginated_tasks = filtered_tasks[start:end]
    task_page_numbers = range(1, task_total_pages + 1)

    messages_res = requests.get(
        f"{OTTO_API_URL}/project/{project_id}/messages",
        headers={"x-api-key": OTTO_API_KEY},
    )
    messages = messages_res.json() if messages_res.status_code == 200 else []
    templates_dir = os.path.join(os.path.dirname(__file__), '../templates/emails/project')
    email_templates = [f[:-5] for f in os.listdir(templates_dir) if f.endswith('.html')]
    personen, agenten = load_person_lists()
    sprints_res = requests.get(
        f"{OTTO_API_URL}/sprints", headers={"x-api-key": OTTO_API_KEY}
    )
    sprints = sprints_res.json() if sprints_res.status_code == 200 else []

    return render(
        request,
        "core/project_detailview.html",
        {
            "projekt": projekt,
            "personen": personen,
            "agenten": agenten,
            "tasks": paginated_tasks,
            "messages": messages,
            "dateien": dateien,
            "status_liste": status_liste,
            "prio_liste": prio_liste,
            "typ_liste": typ_liste,
            "sprints": sprints,
            "sprint_id": sprint_id_filter,
            "task_page": task_page,
            "task_total_pages": task_total_pages,
            "task_page_numbers": task_page_numbers,
            "task_q": task_q,
            "email_templates": email_templates,
        },
    )


@login_required
@csrf_exempt
def delete_project(request):
    if request.method == "POST":
        project_id = request.POST.get("project_id")
        if not project_id:
            return JsonResponse({"error": "Keine Projekt-ID."}, status=400)
        res = requests.delete(
            f"{OTTO_API_URL}/projekte/{project_id}",
            headers={"x-api-key": OTTO_API_KEY},
        )
        if res.status_code == 200:
            if request.headers.get("HX-Request") == "true":
                return HttpResponse("")
            return redirect("/projekt/?deleted=1")
        return JsonResponse({"error": "Fehler beim Löschen."}, status=500)
    return JsonResponse({"error": "Ungültige Methode."}, status=405)


@require_POST
@csrf_exempt
def project_create_task(request):
    data = json.loads(request.body)
    response = requests.post(
        f"{OTTO_API_URL}/tasks",
        headers={"x-api-key": OTTO_API_KEY},
        json={
            "betreff": data["betreff"],
            "beschreibung": "",
            "zuständig": data.get("zuständig", "Otto"),
            "person_id": data.get("person_id"),
            "requester_id": data.get("requester_id"),
            "aufwand": 1,
            "prio": data.get("prio", "mittel"),
            "status": data.get("status", "Offen"),
            "termin": data.get("termin"),
            "project_id": data["project_id"],
            "sprint_id": data.get("sprint_id"),
        },
    )
    return JsonResponse(response.json(), status=response.status_code)


@login_required
@csrf_exempt
def project_upload_file(request, short):
    if request.method != "POST":
        return JsonResponse({"error": "Ungültige Methode."}, status=405)
    uploaded = request.FILES.get("file")
    if not uploaded:
        return JsonResponse({"error": "Keine Datei."}, status=400)
    try:
        res = requests.post(
            f"{OTTO_API_URL}/sharepoint/projekte/{short}/dateien",
            headers={"x-api-key": OTTO_API_KEY},
            files={"file": (uploaded.name, uploaded.read())},
        )
        if res.status_code in (200, 201):
            return JsonResponse(res.json())
        return JsonResponse({"error": "Fehler beim Upload."}, status=res.status_code)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
