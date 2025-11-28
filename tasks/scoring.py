def score_task(task):
    """
    Basic scoring logic
    """

    importance = task.get("importance", 0)
    hours = task.get("estimated_hours", 0)

    score = (importance * 10) - hours

    return score