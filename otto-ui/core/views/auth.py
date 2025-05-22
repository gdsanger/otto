import requests
import bcrypt
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

        res = requests.get(
            f"{OTTO_API_URL}/users",
            params={"username": username},
            headers={"x-api-key": OTTO_API_KEY},
        )
        user = res.json() if res.status_code == 200 else None

        if user and bcrypt.checkpw(password.encode(), user.get("password", "").encode()):
            user.pop("password", None)
            request.session["user"] = user
            return redirect("/")
        else:
            message = "Login fehlgeschlagen – bitte prüfen Sie Ihre Eingaben."

    return render(request, "core/login.html", {"message": message})

def logout_view(request):
    request.session.flush()
    return redirect("/login")
