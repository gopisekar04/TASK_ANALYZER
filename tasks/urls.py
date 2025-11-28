from django.urls import path
from .views import analyze_tasks

urlpatterns = [
    path("analyze/", analyze_tasks)
]