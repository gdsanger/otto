import requests
import os
from django.shortcuts import render, redirect
from dotenv import load_dotenv

load_dotenv()

OTTO_API_KEY = os.getenv("OTTO_API_KEY")
OTTO_API_URL = os.getenv("OTTO_API_URL")

def login_view(request):
    message = ""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        res = requests.post(
            f"{OTTO_API_URL}/login",
            json={"username": username, "password": password},
            headers={"x-api-key": OTTO_API_KEY},
        )
        if res.status_code == 200:
            user = res.json()
            request.session["user"] = user
            return redirect("/")
        else:
            message = "Login fehlgeschlagen – bitte prüfen Sie Ihre Eingaben."

    return render(request, "core/login.html", {"message": message})

def logout_view(request):
    request.session.flush()
    return redirect("/login")
