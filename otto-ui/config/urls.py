from django.contrib import admin
from django.urls import path
from core import views
from core.views.auth import login_view, logout_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('projekt/', views.project_listview, name='projekt_liste'),
    path('project/new/', views.project_create, name='project_create'),
    path("project/delete/", views.delete_project, name="delete_project"),
    path('project/createtask/', views.project_create_task, name='project_create_task'),
    path('project/<str:short>/upload/', views.project_upload_file, name='project_upload_file'),
    path("project/<str:project_id>/", views.project_detailview, name="project_detailview"),
    path('task/', views.task_listview, name='task_liste'),
    path('task/archiv/', views.task_archive_listview, name='task_archiv'),
    path('task/kanban/', views.task_kanban_view, name='task_kanban'),
    path('task/update_status/', views.update_task_status, name='update_task_status'),
    path('task/update_person/', views.update_task_person, name='update_task_person'),
    path('task/update_typ/', views.update_task_typ, name='update_task_typ'),
    path("task/delete/", views.delete_task, name="delete_task"),
    path('task/update/', views.update_task_details, name='update_task_details'),
    path("task/new/", views.task_create, name="task_create"),
    path('task/view/<str:task_id>/', views.task_pageview, name='task_pageview'),
    path('person/', views.person_listview, name='person_liste'),
    path('person/new/', views.person_create, name='person_create'),
    path('person/delete/', views.delete_person, name='delete_person'),
    path('person/<str:person_id>/', views.person_detailview, name='person_detail'),
    path('message/', views.message_listview, name='message_liste'),
    path('message/<str:message_id>/', views.message_detailview, name='message_detail'),
    path('sprint/', views.sprint_listview, name='sprint_liste'),
    path('sprint/new/', views.sprint_create, name='sprint_create'),
    path('sprint/delete/', views.delete_sprint, name='delete_sprint'),
    path('sprint/createtask/', views.sprint_create_task, name='sprint_create_task'),
    path('sprint/<str:sprint_id>/', views.sprint_detailview, name='sprint_detail'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

]
