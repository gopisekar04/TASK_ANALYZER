from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .scoring import validate_tasks, score_tasks, ValidationError, CycleError
from collections import defaultdict
from tasks.models import Task


@csrf_exempt
def add_task(request):
    if request.method != "POST":
        return JsonResponse({
            "error": "Only POST methos allowed"
        })
    
    try:

        data = json.loads(request.body)
        raw_data = data.get("task")
        if not raw_data:
            return JsonResponse({
                "message": "No task provided"
            })

        tasks, Warnings = validate_tasks([raw_data], require_id=False)
        task = tasks[0]

        obj = Task.objects.create(
            title = task["title"],
            due_date=task.get("due_date"),
            estimated_hours=task["estimated_hours"],
            importance=task["importance"],
            dependencies=task["dependencies"]
        )

        return JsonResponse({
            "message": 'Task added successfully',
            "id": obj.id
        })

    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON"
        }, status=400)
    except ValidationError as e:
        return JsonResponse({
            "error": str(e)
        }, status=400)

def build_graph(tasks):
    """
    Returns adjacency list: task -> dependencies
    """
    graph = defaultdict(list)

    for task in tasks:
        graph[task["id"]] = task["dependencies"]

    return graph

def detect_cycle(graph):
    visited = set()
    stack = []
    in_stack = set()

    def dfs(node):
        if node in in_stack:
            # return actual cycle path
            i = stack.index(node)
            cycle_path = stack[i:] + [node]
            raise CycleError(" → ".join(map(str, cycle_path)))

        if node in visited:
            return

        visited.add(node)
        stack.append(node)
        in_stack.add(node)

        for neighbor in graph[node]:
            dfs(neighbor)

        stack.pop()
        in_stack.remove(node)

    for node in graph:
        dfs(node)

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
            mode = request.GET.get("mode", "smart")
            if mode not in ["smart", "fastest", "impact", "deadline"]:
                raise ValidationError("Invalid sort mode")
            
            ranked = score_tasks(tasks, graph, mode)

            return JsonResponse({
                "warnings": Warnings,
                "ranked_tasks": ranked
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

@csrf_exempt
def analyze_db(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET allowed"}, status=405)

    mode = request.GET.get("mode", "smart")
    ALLOWED = {"smart", "fastest", "impact", "deadline"}
    if mode not in ALLOWED:
        return JsonResponse({"error": "Invalid sorting mode"}, status=400)
    
    db_data = Task.objects.all()

    if not db_data.exists():
        return JsonResponse({"ranked_tasks": [], "message": "No tasks available"}, status=200)

    data = [
        {
            "id": t.id,
            "title": t.title,
            "due_date": t.due_date,
            "estimated_hours": t.estimated_hours,
            "importance": t.importance,
            "dependencies": t.dependencies
        }
        for t in db_data
    ]

    try:
        tasks, warnings = validate_tasks(data, require_id=True)

        graph = build_graph(tasks)
        detect_cycle(graph)

        ranked = score_tasks(tasks, graph, mode)
    
        return JsonResponse({
            "mode": mode,
            "warnings": warnings,
            "ranked_tasks": ranked
        })
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)

    except Exception as e:
        return JsonResponse({"error": "Internal server error", "detail": str(e)}, status=500)

@csrf_exempt
def suggest_tasks(request):

    if request.method != "GET":
        return JsonResponse({
            "error": "Only GET method allowed"
        })
    
    mode = request.GET.get("mode", "smart")
    ALLOWED = {"smart", "fastest", "impact", "deadline"}
    if mode not in ALLOWED:
        return JsonResponse({"error": "Invalid sorting mode"}, status=400)
    
    db_data = Task.objects.all()
    if not db_data.exists():
        return JsonResponse({"top_3": [], "message": "No tasks available"}, status=200)


    data = [
        {
            "id": t.id,
            "title": t.title,
            "due_date": t.due_date,
            "estimated_hours": t.estimated_hours,
            "importance": t.importance,
            "dependencies": t.dependencies
        }
        for t in db_data
    ]

    try:
        tasks, warnings = validate_tasks(data, require_id=True)

        graph = build_graph(tasks)
        detect_cycle(graph)

        ranked = score_tasks(tasks, graph, mode)

        executable = [t for t in ranked if t["depth"] == 0]

        # send top 3
        return JsonResponse({
            "mode": mode,
            "warnings": warnings,
            "top_3": executable[:3]
        })

    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)

    except Exception as e:
        return JsonResponse({"error": "Internal server error", "detail": str(e)}, status=500)
    
@csrf_exempt
def clear_tasks(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    Task.objects.all().delete()
    return JsonResponse({"message": "All tasks cleared"})

@csrf_exempt
def list_tasks(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET allowed"}, status=405)

    data = list(Task.objects.values(
        "id", "title", "due_date", "estimated_hours", "importance", "dependencies"
    ))
    return JsonResponse({"tasks": data})