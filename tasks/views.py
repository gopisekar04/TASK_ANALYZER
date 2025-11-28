from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .scoring import score_task


@csrf_exempt
def analyze_tasks(request):
    if request.method != "POST":
        return JsonResponse({
            "error": "Only POST methos allowed"
        })

    try:
        data = json.loads(request.body)
        tasks = data.get("tasks", [])
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON"
        }, status=400)

    results = []

    for task in tasks:
        score = score_task(task)
        results.append({
            "title": task.get("title"),
            "score": score
        })

        return JsonResponse(results, safe=False)