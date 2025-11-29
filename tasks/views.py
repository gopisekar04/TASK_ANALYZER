from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .scoring import validate_tasks, score_tasks, ValidationError, CycleError
from collections import defaultdict


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

            ranked = score_tasks(tasks, graph)

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