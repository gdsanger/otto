from functools import wraps
from django.shortcuts import redirect


def login_required(func):
    """Ensure the user is logged in.

    If the session does not contain a ``user`` entry, redirect to ``/login/``.
    """

    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("user"):
            return redirect("/login/")
        return func(request, *args, **kwargs)

    return wrapper
