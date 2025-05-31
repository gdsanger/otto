import requests
import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from .helpers import login_required
from core.const import status_liste, prio_liste, typ_liste
import os
from dotenv import load_dotenv

load_dotenv()

OTTO_API_KEY = os.getenv("OTTO_API_KEY")
OTTO_API_URL = os.getenv("OTTO_API_URL")

@login_required
def person_listview(request):
    res = requests.get(f"{OTTO_API_URL}/personen", headers={"x-api-key": OTTO_API_KEY})
    personen = res.json() if res.status_code == 200 else []
    q = request.GET.get("q", "").lower()
    if q:
        personen = [p for p in personen if q in p.get("name", "").lower() or q in p.get("email", "").lower()]
    return render(request, "core/person_listview.html", {"personen": personen})

@login_required
@csrf_exempt
def person_detailview(request, person_id):
    if request.method == "POST":
        payload = json.loads(request.body)
        res = requests.get(f"{OTTO_API_URL}/personen/{person_id}", headers={"x-api-key": OTTO_API_KEY})
        if res.status_code != 200:
            return JsonResponse({"error": "Person nicht gefunden"}, status=404)
        person = res.json()
        for k, v in payload.items():
            person[k] = v
        update = requests.put(
            f"{OTTO_API_URL}/personen/{person_id}",
            headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
            data=json.dumps(person)
        )
        return JsonResponse({"success": True}) if update.status_code == 200 else JsonResponse({"error": "Fehler beim Speichern"}, status=500)

    res = requests.get(
        f"{OTTO_API_URL}/personen/{person_id}", headers={"x-api-key": OTTO_API_KEY}
    )
    if res.status_code != 200:
        return render(request, "core/person_detailview.html", {"person": {}, "tasks": []})

    data = res.json()
    tasks = data.get("tasks", [])

    # Filter- und Paging-Parameter
    task_q = request.GET.get("task_q", "").lower()
    show_done = bool(request.GET.get("show_done"))
    try:
        task_page = int(request.GET.get("task_page", 1))
    except ValueError:
        task_page = 1
    task_per_page = 20

    filtered_tasks = []
    for t in tasks:
        status = t.get("status", "").lower()
        if show_done:
            if status != "✅ abgeschlossen".lower():
                continue
        else:
            if status == "✅ abgeschlossen".lower():
                continue
        if task_q and task_q not in t.get("betreff", "").lower() and task_q not in t.get("beschreibung", "").lower():
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

    # Projekte laden, um Namen zuzuordnen
    projekte_res = requests.get(
        f"{OTTO_API_URL}/projekte", headers={"x-api-key": OTTO_API_KEY}
    )
    projekte = projekte_res.json() if projekte_res.status_code == 200 else []
    projekt_map = {p.get("id"): p.get("name") for p in projekte}
    for t in paginated_tasks:
        pid = t.get("project_id")
        t["project_name"] = projekt_map.get(pid, "") if pid else ""

    return render(
        request,
        "core/person_detailview.html",
        {
            "person": data,
            "tasks": paginated_tasks,
            "status_liste": status_liste,
            "prio_liste": prio_liste,
            "typ_liste": typ_liste,
            "task_page": task_page,
            "task_total_pages": task_total_pages,
            "task_page_numbers": task_page_numbers,
            "task_q": task_q,
            "show_done": show_done,
        },
    )


@login_required
@csrf_exempt
def person_create(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            res = requests.post(
                f"{OTTO_API_URL}/personen",
                headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
                data=json.dumps({"personen": [payload]}),
            )
            if res.status_code in (200, 201):
                inserted_id = res.json().get("inserted_ids", [None])[0]
                return JsonResponse({"success": True, "id": inserted_id})
            return JsonResponse({"error": "Fehler beim Speichern"}, status=500)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return render(request, "core/person_detailview.html", {
        "person": {},
        "tasks": [],
        "status_liste": status_liste,
        "prio_liste": prio_liste,
        "typ_liste": typ_liste,
    })


@login_required
@csrf_exempt
def delete_person(request):
    if request.method == "POST":
        person_id = request.POST.get("person_id")
        if not person_id:
            return JsonResponse({"error": "Keine Person-ID."}, status=400)
        res = requests.delete(
            f"{OTTO_API_URL}/personen/{person_id}",
            headers={"x-api-key": OTTO_API_KEY},
        )
        if res.status_code == 200:
            if request.headers.get("HX-Request") == "true":
                return HttpResponse("")
            return HttpResponseRedirect("/person/")
        return JsonResponse({"error": "Fehler beim L\u00f6schen."}, status=500)
    return JsonResponse({"error": "Ung\u00fcltige Methode."}, status=405)
