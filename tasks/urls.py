from django.urls import path
from .views import analyze_tasks, suggest_tasks, add_task, clear_tasks, list_tasks

urlpatterns = [
    path("add/", add_task),
    path("list/", list_tasks),
    path("clear/", clear_tasks),
    path("analyze/", analyze_tasks),
    path("suggest/", suggest_tasks),
]