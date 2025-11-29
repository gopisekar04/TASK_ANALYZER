from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .scoring import validate_tasks, ValidationError


@csrf_exempt
def analyze_tasks(request):
    if request.method != "POST":
        return JsonResponse({
            "error": "Only POST methos allowed"
        })

    try:
        data = json.loads(request.body)
        raw_tasks = data.get("tasks", [])
        if not raw_tasks:
            return JsonResponse({
                "Message": "No tasks available to analyze"
            })
        tasks, Warnings = validate_tasks(raw_tasks)

        return JsonResponse({
            "warnings": Warnings,
            "tasks": tasks
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON"
        }, status=400)
    except ValidationError as e:
        return JsonResponse({

            "error": str(e)
        }, status=400)