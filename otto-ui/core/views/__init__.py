from .auth import login_view, logout_view
from .tasks import task_listview, update_task_status, update_task_person, update_task_details, task_detail_or_update, delete_task, task_create
from .projects import project_listview, project_detailview
from .meetings import meeting_listview, meeting_detailview
from django.shortcuts import render
from .helpers import login_required

@login_required
def home(request):
    return render(request, "core/home.html")

def parse_termin(t):
    from datetime import datetime
    try:
        return datetime.fromisoformat(t["termin"]) if t["termin"] else datetime.max
    except:
        return datetime.max