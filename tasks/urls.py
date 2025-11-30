from django.urls import path
from .views import analyze_tasks, suggest_tasks, add_task, clear_tasks, list_tasks, analyze_db

urlpatterns = [
    path("add/", add_task),
    path("list/", list_tasks),
    path("clear/", clear_tasks),
    path("analyze/", analyze_tasks),
    path("analyze_db/", analyze_db),
    path("suggest/", suggest_tasks),
]