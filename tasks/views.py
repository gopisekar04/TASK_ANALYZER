from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .scoring import validate_tasks, build_graph, detect_cycle, score_tasks, ValidationError, CycleError


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

        """
        build graph and detech cycle
        if cycle exist -> return Error circular dependency detected
        else -> continue with the ranking
        """

        graph = build_graph(tasks)

        try:
            detect_cycle(graph)

            ranked = score_tasks(tasks)

            return JsonResponse({
                "warnings": Warnings,
                "ranked_tasks": ranked,
                "top_3": ranked[:3]
            })
        
        except CycleError as e:
            raise ValidationError(f"Circular dependency detected: {e}")
        
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON"
        }, status=400)
    except ValidationError as e:
        return JsonResponse({
            "error": str(e)
        }, status=400)