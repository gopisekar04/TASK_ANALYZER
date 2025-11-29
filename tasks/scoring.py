from datetime import datetime

class ValidationError(Exception):
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

