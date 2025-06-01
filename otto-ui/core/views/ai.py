import os
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .helpers import login_required
from dotenv import load_dotenv

load_dotenv()

OTTO_API_KEY = os.getenv("OTTO_API_KEY")
OTTO_API_URL = os.getenv("OTTO_API_URL")


@login_required
@csrf_exempt
def improve_description(request):
    if request.method != "POST":
        return JsonResponse({"error": "Ung\u00fcltige Methode."}, status=405)

    text = request.POST.get("text", "").strip()
    html = request.POST.get("html") == "1"
    if not text:
        return JsonResponse({"error": "Kein Text."}, status=400)

    payload = {"text": text}
    if html:
        payload["html"] = True

    res = requests.post(
        f"{OTTO_API_URL}/ai/improve_description",
        headers={"x-api-key": OTTO_API_KEY, "Content-Type": "application/json"},
        data=json.dumps(payload),
    )
    if res.status_code == 200:
        data = res.json()
        return JsonResponse({"text": data.get("text", text)})

    try:
        detail = res.json().get("detail")
    except Exception:
        detail = None
    return JsonResponse({"error": detail or "Fehler bei KI-Anfrage."}, status=res.status_code or 500)
