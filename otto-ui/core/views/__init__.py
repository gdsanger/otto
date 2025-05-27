from .auth import login_view, logout_view
from .tasks import (
    task_listview,
    task_archive_listview,
    update_task_status,
    update_task_person,
    update_task_typ,
    update_task_details,
    delete_task,
    task_create,
    task_pageview,
)
from .projects import (
    project_listview,
    project_detailview,
    delete_project,
    project_create_task,
    project_upload_file,
)
from .meetings import meeting_listview, meeting_detailview, meeting_create
from .persons import person_listview, person_detailview
from django.shortcuts import render
from .helpers import login_required
import os
import requests
import json
from datetime import datetime, timedelta
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

OTTO_API_KEY = os.getenv("OTTO_API_KEY")
OTTO_API_URL = os.getenv("OTTO_API_URL")


@login_required
def home(request):
    q = request.GET.get("q", "").lower()

    # Daten abrufen
    tasks = []
    meetings = []
    projekte = []
    try:
        t_res = requests.get(
            f"{OTTO_API_URL}/tasks", headers={"x-api-key": OTTO_API_KEY}
        )
        if t_res.status_code == 200:
            tasks = t_res.json()
        m_res = requests.get(
            f"{OTTO_API_URL}/meetings", headers={"x-api-key": OTTO_API_KEY}
        )
        if m_res.status_code == 200:
            meetings = m_res.json()
        p_res = requests.get(
            f"{OTTO_API_URL}/projekte", headers={"x-api-key": OTTO_API_KEY}
        )
        if p_res.status_code == 200:
            projekte = p_res.json()
    except Exception:
        pass

    if q:
        tasks = [t for t in tasks if q in t.get("betreff", "").lower()]
        meetings = [m for m in meetings if q in m.get("name", "").lower()]
        projekte = [p for p in projekte if q in p.get("name", "").lower()]

    # Aufgaben nach Status
    status_counter = Counter(t.get("status", "Unbekannt") or "Unbekannt" for t in tasks)
    status_labels = list(status_counter.keys())
    status_values = list(status_counter.values())

    # Anstehende Aufgaben
    now = datetime.now()
    upcoming_tasks = []
    for t in tasks:
        termin_dt = parse_termin(t)
        if termin_dt == datetime.max:
            continue

        status = str(t.get("status", "")).lower()
        is_done = "abgeschlossen" in status or "erledigt" in status

        if now <= termin_dt <= now + timedelta(days=7) or (termin_dt < now and not is_done):
            t["termin_dt"] = termin_dt
            upcoming_tasks.append(t)

    upcoming_tasks.sort(key=lambda x: x["termin_dt"])
    upcoming_tasks = upcoming_tasks[:20]

    # Meetings
    past_meetings = []
    future_meetings = []
    for m in meetings:
        try:
            m_dt = datetime.fromisoformat(m.get("datum")) if m.get("datum") else None
        except Exception:
            m_dt = None
        if not m_dt:
            continue
        if m_dt < now:
            past_meetings.append((m_dt, m))
        elif m_dt <= now + timedelta(days=7):
            future_meetings.append((m_dt, m))
    past_meetings.sort(key=lambda x: x[0], reverse=True)
    future_meetings.sort(key=lambda x: x[0])
    past_meetings = [m for _, m in past_meetings[:3]]
    future_meetings = [m for _, m in future_meetings[:3]]

    # Projektstatus
    tasks_by_project = {}
    for t in tasks:
        pid = t.get("project_id")
        if pid:
            tasks_by_project.setdefault(pid, []).append(t)

    project_status = []
    for p in projekte:
        tid = p.get("id")
        p_tasks = tasks_by_project.get(tid, [])
        offen = len([t for t in p_tasks if t.get("status") != "✅ abgeschlossen"])
        erledigt = len([t for t in p_tasks if t.get("status") == "✅ abgeschlossen"])
        project_status.append(
            {
                "id": tid,
                "name": p.get("name"),
                "short": p.get("short"),
                "typ": p.get("typ"),
                "status": p.get("status"),
                "prio": p.get("prio"),
                "offen": offen,
                "erledigt": erledigt,
            }
        )

    context = {
        "task_status_labels": json.dumps(status_labels),
        "task_status_counts": json.dumps(status_values),
        "upcoming_tasks": upcoming_tasks,
        "past_meetings": past_meetings,
        "future_meetings": future_meetings,
        "project_status": project_status,
        "search_query": q,
        "tasks": tasks,
        "meetings": meetings,
        "projekte": projekte,
    }

    return render(request, "core/home.html", context)


def parse_termin(t):
    from datetime import datetime

    try:
        return datetime.fromisoformat(t["termin"]) if t.get("termin") else datetime.max
    except Exception:
        return datetime.max
