import os
import requests
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .helpers import login_required
from dotenv import load_dotenv

load_dotenv()

OTTO_API_KEY = os.getenv("OTTO_API_KEY")
OTTO_API_URL = os.getenv("OTTO_API_URL")


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
