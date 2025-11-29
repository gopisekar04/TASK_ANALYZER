from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .scoring import validate_tasks, score_tasks, ValidationError, CycleError
from collections import defaultdict
from tasks.models import Task


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
            "task_id": obj.id,
            "warnings": Warnings
        })

    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON"
        }, status=400)
    except ValidationError as e:
        return JsonResponse({
            "error": str(e)
        }, status=400)

@csrf_exempt
def suggest_tasks(request):

    if request.method != "GET":
        return JsonResponse({
            "error": "Only GET method allowed"
        })
    db_data = Task.objects.all()

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

    return JsonResponse({
        "Message": "/suggest route",
        "tasks": data
    })