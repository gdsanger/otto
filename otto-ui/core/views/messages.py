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
def message_detailview(request, message_id):
    res = requests.get(
        f"{OTTO_API_URL}/messages/{message_id}",
        headers={"x-api-key": OTTO_API_KEY},
    )
    message = res.json() if res.status_code == 200 else {}
    return render(request, "core/message_detailview.html", {"message": message})
