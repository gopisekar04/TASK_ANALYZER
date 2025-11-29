from datetime import datetime, date
from collections import defaultdict

class ValidationError(Exception):
    pass 

class CycleError(Exception):
    pass

def validate_tasks(tasks, require_id=True):

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
            raise ValidationError("Task must be an object")

        # Required base fields
        required = ["title", "estimated_hours", "dependencies"]
        if require_id:
            required = ["id"] + required

        for field in required:
            if field not in task:
                raise ValidationError(f"Task {index+1}: missing field '{field}'")

        # Handle ID only if required
        task_id = None
        if require_id:
            task_id = task["id"]
            if not isinstance(task_id, (str, int)):
                raise ValidationError("id must be string or number")
            if task_id in seen_ids:
                raise ValidationError(f"Duplicate task id: {task_id}")
            seen_ids.add(task_id)

        # Title
        if not isinstance(task["title"], str) or not task["title"].strip():
            raise ValidationError("Invalid title")

        # Estimated hours
        hours = task["estimated_hours"]
        if not isinstance(hours, int) or hours <= 0:
            raise ValidationError("estimated_hours must be positive integer")

        # Importance (default)
        importance = task.get("importance")
        if importance is None:
            task["importance"] = 5
            Warnings.append(f"'{task['title']}': importance defaulted to 5")
        elif not isinstance(importance, int) or not (1 <= importance <= 10):
            raise ValidationError("importance must be integer 1-10")

        # Due date (optional)
        due = task.get("due_date")
        if due:
            try:
                task["due_date"] = datetime.strptime(due, "%Y-%m-%d").date()
                if task["due_date"] < date.today():
                    Warnings.append(f"'{task['title']}': task is overdue")
            except ValueError:
                raise ValidationError("invalid due_date format (use YYYY-MM-DD)")
        else:
            task["due_date"] = None
            Warnings.append(f"'{task['title']}': due_date missing")


        # Dependencies
        deps = task["dependencies"]
        if not isinstance(deps, list):
            raise ValidationError("dependencies must be a list")

        if require_id and task_id in deps:
            raise ValidationError("task cannot depend on itself")

        normalized.append(task)

    # Dependency existence check (only when IDs required)
    if require_id:
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

BLOCKED_PENALTY = 0.4

PRIORITY_RANGE = {
    0.75: "High"
}

SMART_WEIGHT = {
    "urgency": 0.40,
    "importance": 0.25,
    "dependency": 0.20,
    "effort": 0.15
}

FAST_WEIGHT = {
    "effort": 0.50,
    "urgency": 0.20,
    "importance": 0.15,
    "dependency": 0.10
}

IMPACT_WEIGHT = {
    "importance": 0.50,
    "dependency": 0.25,
    "urgency": 0.15,
    "effort": 0.10
}

DEADLINE_WEIGHT = {
    "urgency": 0.55,
    "importance": 0.20,
    "dependency": 0.15,
    "effort": 0.10
}

WEIGHT_METHOD = {
    "smart": SMART_WEIGHT,
    "fastest": FAST_WEIGHT,
    "impact": IMPACT_WEIGHT,
    "deadline": DEADLINE_WEIGHT
}

def compute_depth(task_id, graph, memo):
    if task_id not in graph or not graph[task_id]:
        return 0

    if task_id in memo:
        return memo[task_id]

    memo[task_id] = 1 + max(compute_depth(dep, graph, memo) for dep in graph[task_id])
    return memo[task_id]


def score_tasks(tasks, graph, mode):
    dependents_map = build_dependents_map(tasks)
    depth_cache = {}
    results = []
    WEIGHTS = WEIGHT_METHOD[mode]

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
            "due_date": task["due_date"],
            "effort": task["estimated_hours"],
            "importance": task["importance"],
            "score": round(priority_score, 2),
            "priority_indicator": "High" if priority_score >= 0.75 else "Medium" if priority_score >= 0.40 else "Low",
            "depth": depth,
            "urgency_score": urgent_score,
            "importance_score": important_score,
            "effort_score": effor_score,
            "dependency_score": dependency_score,
            "reasons": reasons
        })

    if mode == "fastest":
        results.sort(key=lambda x: (x["depth"], -x["effort_score"]))
    elif mode == "impact":
        results.sort(key=lambda x: (x["depth"], -x["importance_score"]))
    elif mode == "deadline":
        results.sort(key=lambda x: (x["depth"], -x["urgency_score"]))
    else:
        results.sort(key=lambda x: (x["depth"], -x["score"]))

    final_modified_result = [{
        "id": task["id"],
        "title": task["title"],
        "due_date": task["due_date"],
        "effort": task["effort"],
        "importance": task["importance"],
        "priority_score": task["score"],
        "priority_indicator": task["priority_indicator"],
        "reasons": reasons
    } for task in results]


    return final_modified_result