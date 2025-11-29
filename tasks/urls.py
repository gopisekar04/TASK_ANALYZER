from django.urls import path
from .views import analyze_tasks, suggest_tasks, add_task

urlpatterns = [
    path("analyze/", analyze_tasks),
    path("suggest/", suggest_tasks),
    path("add/", add_task)
]