import os
import json
import requests
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
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

    messages = [m for m in msgs if m.get("direction") == ("in" if folder == "in" else "out")]

    selected = None
    if selected_id:
        res_det = requests.get(f"{OTTO_API_URL}/messages/{selected_id}", headers={"x-api-key": OTTO_API_KEY})
        if res_det.status_code == 200:
            selected = res_det.json()

    return render(request, "core/message_listview.html", {
        "messages": messages,
        "folder": folder,
        "selected": selected,
    })

@login_required
def message_detailview(request, message_id):
    res = requests.get(
        f"{OTTO_API_URL}/messages/{message_id}",
        headers={"x-api-key": OTTO_API_KEY},
    )
    message = res.json() if res.status_code == 200 else {}
    return render(request, "core/message_detailview.html", {"message": message})


@login_required
@csrf_exempt
def send_message(request):
    if request.method == "POST":
        message_id = request.POST.get("message_id")
        if not message_id:
            return JsonResponse({"error": "Keine Message-ID."}, status=400)

        res = requests.get(f"{OTTO_API_URL}/messages/{message_id}", headers={"x-api-key": OTTO_API_KEY})
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
