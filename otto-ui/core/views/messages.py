import os
import json
import requests
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from .helpers import login_required
from dotenv import load_dotenv

load_dotenv()

OTTO_API_KEY = os.getenv("OTTO_API_KEY")
OTTO_API_URL = os.getenv("OTTO_API_URL")
GRAPH_API_URL = os.getenv("GRAPH_API_URL", "https://graph.isarlabs.de")


@login_required
def message_listview(request):
    folder = request.GET.get("folder", "in")
    selected_id = request.GET.get("message_id")

    res = requests.get(f"{OTTO_API_URL}/messages", headers={"x-api-key": OTTO_API_KEY})
    msgs = res.json() if res.status_code == 200 else []

    proj_res = requests.get(
        f"{OTTO_API_URL}/projekte", headers={"x-api-key": OTTO_API_KEY}
    )
    projekte = proj_res.json() if proj_res.status_code == 200 else []

    if folder == "archiv":
        messages = [
            m
            for m in msgs
            if m.get("direction") == "in" and m.get("status") == "archiviert"
        ]
    elif folder == "in":
        messages = [
            m
            for m in msgs
            if m.get("direction") == "in" and m.get("status") != "archiviert"
        ]
    else:
        messages = [m for m in msgs if m.get("direction") == "out"]

    for m in messages:
        try:
            m["_datum"] = (
                datetime.fromisoformat(m.get("datum"))
                if m.get("datum")
                else datetime.min
            )
        except Exception:
            m["_datum"] = datetime.min
    messages.sort(key=lambda m: m["_datum"], reverse=True)

    selected = None
    similar_tasks = []
    if selected_id:
        res_det = requests.get(
            f"{OTTO_API_URL}/messages/{selected_id}",
            headers={"x-api-key": OTTO_API_KEY},
        )
        if res_det.status_code == 200:
            selected = res_det.json()
            # try to determine requester_id based on sender address
            sender_addr = (selected.get("sender") or selected.get("from") or "").lower()
            if sender_addr:
                personen_res = requests.get(
                    f"{OTTO_API_URL}/personen",
                    headers={"x-api-key": OTTO_API_KEY},
                )
                if personen_res.status_code == 200:
                    for p in personen_res.json():
                        if p.get("email", "").lower() == sender_addr:
                            selected["requester_id"] = p.get("id")
                            break
            sim_res = requests.get(
                f"{OTTO_API_URL}/messages/{selected_id}/similar_tasks",
                headers={"x-api-key": OTTO_API_KEY},
            )
            if sim_res.status_code == 200:
                similar_tasks = sim_res.json()

    return render(
        request,
        "core/message_listview.html",
        {
            "messages": messages,
            "folder": folder,
            "selected": selected,
            "similar_tasks": similar_tasks,
            "projekte": projekte,
        },
    )


@login_required
@csrf_exempt
def message_detailview(request, message_id):
    if request.method == "POST":
        payload = json.loads(request.body)
        res = requests.get(
            f"{OTTO_API_URL}/messages/{message_id}", headers={"x-api-key": OTTO_API_KEY}
        )
        if res.status_code != 200:
            return JsonResponse({"error": "Nachricht nicht gefunden."}, status=404)
        message = res.json()
        payload.setdefault("to", "")
        payload.setdefault("cc", "")
        message.update(
            {
                "subject": payload.get("subject", message.get("subject")),
                "message": payload.get("message", message.get("message")),
                "to": [
                    a.strip() for a in payload.get("to", "").split(",") if a.strip()
                ],
                "cc": [
                    a.strip() for a in payload.get("cc", "").split(",") if a.strip()
                ],
            }
        )
        update = requests.put(
            f"{OTTO_API_URL}/messages/{message_id}",
            headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
            data=json.dumps(message),
        )
        return (
            JsonResponse({"success": True})
            if update.status_code == 200
            else JsonResponse({"error": "Fehler beim Speichern"}, status=500)
        )

    res = requests.get(
        f"{OTTO_API_URL}/messages/{message_id}",
        headers={"x-api-key": OTTO_API_KEY},
    )
    message = res.json() if res.status_code == 200 else {}

    sim_res = requests.get(
        f"{OTTO_API_URL}/messages/{message_id}/similar_tasks",
        headers={"x-api-key": OTTO_API_KEY},
    )
    similar_tasks = sim_res.json() if sim_res.status_code == 200 else []

    return render(
        request,
        "core/message_editview.html",
        {"message": message, "similar_tasks": similar_tasks},
    )


@login_required
@csrf_exempt
def message_create(request):
    if request.method == "POST":
        payload = json.loads(request.body)
        data = {
            "datum": datetime.utcnow().isoformat(),
            "subject": payload.get("subject", ""),
            "to": [a.strip() for a in payload.get("to", "").split(",") if a.strip()],
            "cc": [a.strip() for a in payload.get("cc", "").split(",") if a.strip()],
            "message": payload.get("message", ""),
            "direction": payload.get("direction", "out"),
            "status": payload.get("status", "neu"),
            "project_id": payload.get("project_id"),
            "task_id": payload.get("task_id"),
            "sprint_id": payload.get("sprint_id"),
        }
        res = requests.post(
            f"{OTTO_API_URL}/messages",
            headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
            data=json.dumps(data),
        )
        if res.status_code in (200, 201):
            return JsonResponse({"success": True, "id": res.json().get("id")})
        return JsonResponse({"error": "Fehler beim Speichern"}, status=500)

    message = {
        "direction": "out",
        "status": "neu",
    }
    template = request.GET.get("template")
    project_id = request.GET.get("project_id")
    task_id = request.GET.get("task_id")
    if template and task_id:
        t_res = requests.get(
            f"{OTTO_API_URL}/tasks/{task_id}",
            headers={"x-api-key": OTTO_API_KEY},
        )
        task = t_res.json() if t_res.status_code == 200 else {}
        project_id = task.get("project_id")
        projekt = {}
        if project_id:
            p_res = requests.get(
                f"{OTTO_API_URL}/projekte/{project_id}",
                headers={"x-api-key": OTTO_API_KEY},
            )
            if p_res.status_code == 200:
                projekt = p_res.json()

        personen_res = requests.get(
            f"{OTTO_API_URL}/personen",
            headers={"x-api-key": OTTO_API_KEY},
        )
        personen = personen_res.json() if personen_res.status_code == 200 else []
        person_map = {p.get("id"): p for p in personen}

        to_list = []
        bearer = person_map.get(task.get("person_id"))
        if bearer and bearer.get("email"):
            to_list.append(bearer["email"])

        cc_set = set()
        requester = person_map.get(task.get("requester_id"))
        if requester and requester.get("email") and requester["email"] not in to_list:
            cc_set.add(requester["email"])

        proj_bearbeiter = None
        if projekt:
            proj_bearbeiter = person_map.get(projekt.get("bearbeiter"))
            if (
                proj_bearbeiter
                and proj_bearbeiter.get("email")
                and proj_bearbeiter["email"] not in to_list
            ):
                cc_set.add(proj_bearbeiter["email"])

        html = render_to_string(
            f"emails/task/{template}.html",
            {
                "projekt": projekt,
                "task": task,
                "requester": requester,
            },
        )
        message.update(
            {
                "task_id": task_id,
                "project_id": project_id,
                "subject": f"Task-Update: {task.get('betreff', '')}",
                "message": html,
                "to": to_list,
                "cc": list(cc_set),
            }
        )

    elif template and project_id:
        p_res = requests.get(
            f"{OTTO_API_URL}/projekte/{project_id}", headers={"x-api-key": OTTO_API_KEY}
        )
        projekt = p_res.json() if p_res.status_code == 200 else {}

        # parse planned completion date for proper formatting in template
        date_str = projekt.get("geplante_fertigstellung")
        if date_str:
            try:
                projekt["geplante_fertigstellung"] = datetime.fromisoformat(
                    date_str
                ).date()
            except ValueError:
                projekt["geplante_fertigstellung"] = None

        t_res = requests.get(
            f"{OTTO_API_URL}/project/{project_id}/tasks",
            headers={"x-api-key": OTTO_API_KEY},
        )
        tasks = t_res.json() if t_res.status_code == 200 else []

        offene_tasks = []
        erledigte_tasks = []
        now = datetime.utcnow().date()

        for t in tasks:
            termin_str = t.get("termin")
            if termin_str:
                try:
                    t["termin"] = datetime.fromisoformat(termin_str).date()
                except ValueError:
                    t["termin"] = None

            erledigt_str = t.get("erledigt")
            erledigt_dt = None
            if erledigt_str:
                try:
                    erledigt_dt = datetime.fromisoformat(erledigt_str).date()
                    t["erledigt"] = erledigt_dt
                except ValueError:
                    erledigt_dt = None
                    t["erledigt"] = None

            if t.get("status") == "✅ abgeschlossen":
                if erledigt_dt and (now - erledigt_dt).days <= 7:
                    erledigte_tasks.append(t)
            else:
                offene_tasks.append(t)

        # Empfänger ermitteln
        personen_res = requests.get(
            f"{OTTO_API_URL}/personen", headers={"x-api-key": OTTO_API_KEY}
        )
        personen = personen_res.json() if personen_res.status_code == 200 else []
        person_map = {p.get("id"): p for p in personen}

        to_list = []
        for pid in projekt.get("stakeholder_ids", []):
            person = person_map.get(pid)
            if person and person.get("email"):
                to_list.append(person["email"])

        cc_list = []
        bearbeiter_id = projekt.get("bearbeiter")
        if bearbeiter_id:
            person = person_map.get(bearbeiter_id)
            if person and person.get("email"):
                cc_list.append(person["email"])

        html = render_to_string(
            f"emails/project/{template}.html",
            {
                "projekt": projekt,
                "aufgaben": offene_tasks,
                "erledigte_aufgaben": erledigte_tasks,
            },
        )
        message.update(
            {
                "project_id": project_id,
                "subject": f"Projektzusammenfassung: {projekt.get('name', '')}",
                "message": html,
                "to": to_list,
                "cc": cc_list,
            }
        )

    return render(request, "core/message_editview.html", {"message": message})


@login_required
@csrf_exempt
def send_message(request):
    if request.method == "POST":
        message_id = request.POST.get("message_id")
        if not message_id:
            return JsonResponse({"error": "Keine Message-ID."}, status=400)

        res = requests.get(
            f"{OTTO_API_URL}/messages/{message_id}", headers={"x-api-key": OTTO_API_KEY}
        )
        if res.status_code != 200:
            return JsonResponse({"error": "Nachricht nicht gefunden."}, status=404)

        msg = res.json()

        params = {
            "subject": msg.get("subject", ""),
            "body": msg.get("message", ""),
            "to": ",".join(msg.get("to", [])),
        }
        if msg.get("cc"):
            params["cc"] = ",".join(msg.get("cc"))

        send_res = requests.post(
            f"{GRAPH_API_URL}/mail",
            headers={"x-api-key": OTTO_API_KEY},
            params=params,
        )

        if send_res.status_code == 200:
            msg["status"] = "gesendet"
            requests.put(
                f"{OTTO_API_URL}/messages/{message_id}",
                headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
                data=json.dumps(msg),
            )
            if request.headers.get("HX-Request") == "true":
                return HttpResponse("")
            return redirect(request.META.get("HTTP_REFERER", "/message/"))

        msg["status"] = "fehler"
        requests.put(
            f"{OTTO_API_URL}/messages/{message_id}",
            headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
            data=json.dumps(msg),
        )
        return JsonResponse({"error": "Fehler beim Senden."}, status=500)

    return JsonResponse({"error": "Ungültige Methode."}, status=405)


@login_required
@csrf_exempt
def fetch_messages(request):
    """Trigger the backend to fetch new inbox messages."""
    if request.method != "POST":
        return JsonResponse({"error": "Ungültige Methode."}, status=405)

    res = requests.post(
        f"{OTTO_API_URL}/messages/fetch",
        headers={"x-api-key": OTTO_API_KEY},
    )

    if res.status_code == 200:
        if request.headers.get("HX-Request") == "true":
            return HttpResponse("")
        return redirect(request.META.get("HTTP_REFERER", "/message/"))

    return JsonResponse({"error": "Fehler beim Abrufen."}, status=500)


@login_required
@csrf_exempt
def update_message_project(request):
    if request.method == "POST":
        message_id = request.POST.get("message_id")
        project_id = request.POST.get("project_id") or None

        if not message_id:
            return JsonResponse({"error": "Keine Message-ID."}, status=400)

        res = requests.get(
            f"{OTTO_API_URL}/messages/{message_id}",
            headers={"x-api-key": OTTO_API_KEY},
        )
        if res.status_code != 200:
            return JsonResponse({"error": "Nachricht nicht gefunden."}, status=404)

        message = res.json()
        message["project_id"] = project_id
        update = requests.put(
            f"{OTTO_API_URL}/messages/{message_id}",
            headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
            data=json.dumps(message),
        )
        return (
            HttpResponse("OK")
            if update.status_code == 200
            else JsonResponse({"error": "Fehler beim Speichern."}, status=500)
        )

    return JsonResponse({"error": "Ungültige Methode."}, status=405)


@login_required
@csrf_exempt
def update_message_status(request):
    if request.method == "POST":
        message_id = request.POST.get("message_id")
        new_status = request.POST.get("status")
        if not message_id:
            return JsonResponse({"error": "Keine Message-ID."}, status=400)

        res = requests.get(
            f"{OTTO_API_URL}/messages/{message_id}",
            headers={"x-api-key": OTTO_API_KEY},
        )
        if res.status_code != 200:
            return JsonResponse({"error": "Nachricht nicht gefunden."}, status=404)

        message = res.json()
        message["status"] = new_status
        update = requests.put(
            f"{OTTO_API_URL}/messages/{message_id}",
            headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
            data=json.dumps(message),
        )
        if update.status_code == 200:
            if request.headers.get("HX-Request") == "true":
                return HttpResponse("")
            return redirect(request.META.get("HTTP_REFERER", "/message/"))
        return JsonResponse({"error": "Fehler beim Speichern."}, status=500)
    return JsonResponse({"error": "Ungültige Methode."}, status=405)


@login_required
@csrf_exempt
def delete_message(request):
    if request.method == "POST":
        message_id = request.POST.get("message_id")
        if not message_id:
            return JsonResponse({"error": "Keine Message-ID."}, status=400)
        res = requests.delete(
            f"{OTTO_API_URL}/messages/{message_id}",
            headers={"x-api-key": OTTO_API_KEY},
        )
        if res.status_code == 200:
            if request.headers.get("HX-Request") == "true":
                return HttpResponse("")
            return redirect("/message/?deleted=1")
        return JsonResponse({"error": "Fehler beim Löschen."}, status=500)
    return JsonResponse({"error": "Ungültige Methode."}, status=405)
