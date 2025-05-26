from collections import defaultdict
from datetime import datetime, timedelta
from django.shortcuts import render
import os, json, requests
from .views.helpers import login_required
from dotenv import load_dotenv

load_dotenv()

OTTO_API_KEY = os.getenv("OTTO_API_KEY")
OTTO_API_URL = os.getenv("OTTO_API_URL")

@login_required
def home(request):
    q = request.GET.get("q", "").lower()

    tasks, meetings, projekte = [], [], []
    try:
        t_res = requests.get(f"{OTTO_API_URL}/tasks", headers={"x-api-key": OTTO_API_KEY})
        if t_res.status_code == 200:
            tasks = t_res.json()
        m_res = requests.get(f"{OTTO_API_URL}/meetings", headers={"x-api-key": OTTO_API_KEY})
        if m_res.status_code == 200:
            meetings = m_res.json()
        p_res = requests.get(f"{OTTO_API_URL}/projekte", headers={"x-api-key": OTTO_API_KEY})
        if p_res.status_code == 200:
            projekte = p_res.json()
    except Exception:
        pass

    if q:
        tasks = [t for t in tasks if q in t.get("betreff", "").lower()]
        meetings = [m for m in meetings if q in m.get("name", "").lower()]
        projekte = [p for p in projekte if q in p.get("name", "").lower()]

    status_mapping = {
        "abgeschlossen": ("Abgeschlossen", "#4CAF50"),
        "erledigt": ("Abgeschlossen", "#4CAF50"),
        "✔️ abgeschlossen": ("Abgeschlossen", "#4CAF50"),
        "offen": ("Offen", "#FFC107"),
        "Offen": ("Offen", "#FFC107"),
        "neu": ("Offen", "#FFC107"),
        "in arbeit": ("In Arbeit", "#2196F3"),
        "in_arbeit": ("In Arbeit", "#2196F3"),
        "wartet": ("Wartet", "#9E9E9E"),
        "laufend": ("Laufend", "#673AB7"),
        "in planung": ("Geplant", "#FF5722"),
        "specification": ("Geplant", "#FF5722"),
    }

    grouped_status = defaultdict(int)
    color_mapping = {}
    for t in tasks:
        status = t.get("status", "Unbekannt").lower()
        label, color = status_mapping.get(status, ("Sonstige", "#cccccc"))
        grouped_status[label] += 1
        color_mapping[label] = color

    grouped_labels = list(grouped_status.keys())
    grouped_counts = list(grouped_status.values())
    grouped_colors = [color_mapping[k] for k in grouped_labels]

    now = datetime.now()
    upcoming_tasks = []
    for t in tasks:
        termin_dt = parse_termin(t)
        if termin_dt != datetime.max and now <= termin_dt <= now + timedelta(days=7):
            t["termin_dt"] = termin_dt
            upcoming_tasks.append(t)
    upcoming_tasks.sort(key=lambda x: x["termin_dt"])

    past_meetings, future_meetings = [], []
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

    tasks_by_project = defaultdict(list)
    for t in tasks:
        pid = t.get("project_id")
        if pid:
            tasks_by_project[pid].append(t)

    project_status = []
    for p in projekte:
        tid = p.get("id")
        p_tasks = tasks_by_project.get(tid, [])
        offen = len([t for t in p_tasks if t.get("status") != "✅ abgeschlossen"])
        erledigt = len([t for t in p_tasks if t.get("status") == "✅ abgeschlossen"])
        project_status.append({
            "id": tid,
            "name": p.get("name"),
            "status": p.get("status"),
            "prio": p.get("prio"),
            "offen": offen,
            "erledigt": erledigt
        })

    context = {
        "grouped_status_labels": json.dumps(grouped_labels),
        "grouped_status_counts": json.dumps(grouped_counts),
        "grouped_status_colors": json.dumps(grouped_colors),
        "upcoming_tasks": upcoming_tasks,
        "past_meetings": past_meetings,
        "future_meetings": future_meetings,
        "project_status": project_status,
        "search_query": q,
        "tasks": tasks,
        "meetings": meetings,
        "projekte": projekte
    }

    return render(request, "core/home.html", context)

def parse_termin(t):
    try:
        return datetime.fromisoformat(t["termin"]) if t["termin"] else datetime.max
    except:
        return datetime.max
