from django.contrib import admin
from django.urls import path
from core import views
from core.views.auth import login_view, logout_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('projekt/', views.project_listview, name='projekt_liste'),
    path("project/delete/", views.delete_project, name="delete_project"),
    path('project/createtask/', views.project_create_task, name='project_create_task'),   
    path("project/<str:project_id>/", views.project_detailview, name="project_detailview"),  
    path('task/', views.task_listview, name='task_liste'),
    path('task/archiv/', views.task_archive_listview, name='task_archiv'),
    path('task/update_status/', views.update_task_status, name='update_task_status'),
    path('task/update_person/', views.update_task_person, name='update_task_person'),
    path('task/update_typ/', views.update_task_typ, name='update_task_typ'),
    path("task/delete/", views.delete_task, name="delete_task"),
    path('task/update/', views.update_task_details, name='update_task_details'),
    path("task/new/", views.task_create, name="task_create"),
    path('task/view/<str:task_id>/', views.task_pageview, name='task_pageview'),
    path('meeting/', views.meeting_listview, name='meeting_liste'),
    path('meeting/new/', views.meeting_create, name='meeting_create'),
    path('meeting/<str:meeting_id>/', views.meeting_detailview, name='meeting_detail'),
    path('person/', views.person_listview, name='person_liste'),
    path('person/<str:person_id>/', views.person_detailview, name='person_detail'),
    path('message/<str:message_id>/', views.message_detailview, name='message_detail'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

]
