from datetime import datetime, date
from collections import defaultdict

class ValidationError(Exception):
    pass 

class CycleError(Exception):
    pass

def validate_tasks(tasks):

    """
    validate the list of tasks.
    Apply safe defaults for missing values
    Return: (normalized_tasks, warnings)
    Raise validationError on missing required fields 
    """

    if not isinstance(tasks, list):
        raise ValidationError("tasks must be a list")

    normalized = []
    Warnings = []
    seen_ids = set()

    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise ValidationError(f"Task must be an object")
        

        required = ["id", "title", "estimated_hours", "dependencies"]
        for field in required:
            if field not in task:
                raise ValidationError(f"Task {task.get('title', index+1)} missing field: {field}")
        
        task_id = task["id"]
        if not isinstance(task_id, (str, int)):
            raise ValidationError("Id must be string or number")
        if task_id in seen_ids:
            raise ValidationError(f"Duplicate task id: {task_id}")
        seen_ids.add(task_id)

        if not isinstance(task["title"], str) or not task["title"].strip():
            raise ValidationError(f"Task {task_id}: Invalid title")
        
        hours = task["estimated_hours"]
        if not isinstance(hours, int) or hours <= 0:
            raise ValidationError(f"Task {task_id}: estimated_hours must be positive integer")
        
        importance = task.get("importance")
        if importance is None:
            task["importance"] = 5
            Warnings.append(f"Task {task_id}: importance missing, defaulted to 5")
        elif not isinstance(importance, int) or not (1 <= importance <= 10):
            raise ValidationError(f"Task {task_id}: importance must be integer 1-10")
        
        due = task.get("due_date")
        if due:
            try:
                task["due_date"] = datetime.strptime(due, "%Y-%m-%d").date()
            except ValueError:
                raise ValidationError(f"Task {task_id}: invalid due_date format (use YYYY-MM-DD)")
        else:
            Warnings.append(f"Task {task_id}: due_date is missing")
            task["due_date"] = None

        
        deps = task["dependencies"]
        if not isinstance(deps, list):
            raise ValidationError(f"Task {task_id}: dependencies must be a list")

        if task_id in deps:
            raise ValidationError(f"Task {task_id}: cannot depend on itself")

        normalized.append(task)

    all_ids = {task["id"] for task in normalized}
    for task in normalized:
        for dep in task["dependencies"]:
            if dep not in all_ids:
                raise ValidationError(f"Task {task['id']}: unknown dependency '{dep}'")

    return normalized, Warnings

def urgent_score_fun(due_date):
    if not due_date:
        return 0.05
    
    days_left = (due_date - date.today()).days

    if days_left < 0: # Overdue
        return 1.00
    elif days_left == 0: # Due today
        return 0.95
    elif days_left == 1: # Due tomorrow
        return 0.85
    elif 2 <= days_left <= 3:
        return 0.65
    elif 4 <= days_left <= 7:
        return 0.40
    elif 8 <= days_left <= 14:
        return 0.20
    return 0.10

def important_score_fun(importance):
    # normalize the user given importance

    return importance/10

def effor_score_fun(estimated_hours):
    # lesser the time required to complete the task higher the effort_score

    if estimated_hours <= 1:
        return 1.00
    elif 2 <= estimated_hours <= 4:
        return 0.70
    elif 5 <= estimated_hours <= 8:
        return 0.40
    return 0.20

def dependency_score_fun(no_of_dependents):
    # more dependent tasks higher priority

    if no_of_dependents == 0:
        return 0.0
    elif no_of_dependents == 1:
        return 0.4
    elif no_of_dependents == 2:
        return 0.7
    return 1.0

def build_dependents_map(tasks):
    depentents = defaultdict(list)

    for task in tasks:
        for dep in task["dependencies"]:
            depentents[dep].append(task["id"])

    return depentents

def is_blocked(task):
    return len(task["dependencies"]) > 0

WEIGHTS = {
    "urgency": 0.40,
    "importance": 0.25,
    "dependency": 0.20,
    "effort": 0.15
}

BLOCKED_PENALTY = 0.4

PRIORITY_RANGE = {
    0.75: "High"
}


def compute_depth(task_id, graph, memo):
    if task_id not in graph or not graph[task_id]:
        return 0

    if task_id in memo:
        return memo[task_id]

    memo[task_id] = 1 + max(compute_depth(dep, graph, memo) for dep in graph[task_id])
    return memo[task_id]


def score_tasks(tasks, graph):
    dependents_map = build_dependents_map(tasks)
    depth_cache = {}
    results = []

    for task in tasks:
        urgent_score = urgent_score_fun(task["due_date"])
        important_score = important_score_fun(task["importance"])
        effor_score = effor_score_fun(task["estimated_hours"])
        dependency_score = dependency_score_fun(len(dependents_map[task["id"]]))

        priority_score = (
            urgent_score * WEIGHTS["urgency"] +
            important_score * WEIGHTS["importance"] + 
            effor_score * WEIGHTS["effort"] +
            dependency_score * WEIGHTS["dependency"]
        )

        blocked = is_blocked(task)
        if blocked:
            priority_score *= BLOCKED_PENALTY

        depth = compute_depth(task["id"], graph, depth_cache)

        reasons = []
        if urgent_score >= 0.85:
            if urgent_score == 1.0:
                reasons.append(f"Deadline crossed")
            else:
                reasons.append(f"Urgent Deadline {task["due_date"]}")
        if important_score >= 0.8:
            reasons.append("High importance")
        if effor_score >= 0.7:
            reasons.append("Quick win")
        if dependency_score >= 0.7:
            reasons.append("Unblocks other tasks")  
        if blocked:
            reasons.append(f"Currently blocked by task/s {task["dependencies"]}")
        
        results.append({
            "id": task["id"],
            "title": task["title"],
            "score": round(priority_score, 2),
            "priority_indicator": "High" if priority_score >= 0.75 else "Medium" if priority_score >= 0.40 else "Low",
            "depth": depth,
            "reasons": reasons
        })

    results.sort(key=lambda x: (x["depth"], -x["score"]))

    return results