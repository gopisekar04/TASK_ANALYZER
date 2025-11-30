# Task Analyzer

Task Analyzer is a Django mini-project that prioritizes tasks using an intelligent scoring system.
It doesn’t just sort by dates - it reasons about urgency, importance, effort, and dependencies to recommend what you should do first.

---

## Features

* Intelligent scoring (urgency, importance, effort, dependency impact)
* Dependency graph with cycle detection
* Depth-aware ordering (blocked tasks never outrank blockers)
* Multiple priority modes:

  * Smart Balance
  * Fastest Wins
  * High Impact
  * Deadline Driven
* Database-backed tasks (SQLite)
* “Suggest today’s work” endpoint (top 3 executable tasks)
* Validation with warnings for missing but safe defaults
* Unit tests

---

## What a Task Contains

Each task has:

* `title`
* `due_date` (optional)
* `estimated_hours`
* `importance` (1–10)
* `dependencies` (list of task IDs)

---

## How Priority Is Computed

Each task receives four scores that are combined into a final **priority_score**.

### 1) Urgency Score (based on due date)

| Condition | Score |
| --------- | ----- |
| Overdue   | 1.00  |
| Today     | 0.95  |
| Tomorrow  | 0.85  |
| 2–3 days  | 0.65  |
| 4–7 days  | 0.40  |
| 8–14 days | 0.20  |
| > 14 days | 0.10 |

### 2) Importance Score

`importance_score = importance / 10`

### 3) Effort Score (quick wins rise)

| Hours | Score |
| ----- | ----- |
| ≤ 1   | 1.00  |
| 2–4   | 0.70  |
| 5–8   | 0.40  |
| > 8 | 0.20 |

### 4) Dependency Score (impact of unblocking)

| Dependents | Score |
| ---------- | ----- |
| 0          | 0.00  |
| 1          | 0.40  |
| 2          | 0.70  |
| >= 3        | 1.00  |

### Final Formula (Smart Balance)

```
priority_score =
    urgency_score    * 0.40 +
    importance_score * 0.25 +
    dependency_score * 0.20 +
    effort_score     * 0.15
```

---

## Dependency Safety

* A dependency graph is built from all tasks.
* Cycles are detected using DFS; if a cycle exists, the request is rejected.
* Each task gets a **depth** (distance from being executable).
* Sorting always enforces: `(depth ASC, score DESC)` so blocked tasks never float above their dependencies.

---

## Sorting Modes

The same engine powers four modes by changing weights and sort key:

* **Smart Balance**: weighted blend (default)
* **Fastest Wins**: favors effort
* **High Impact**: favors importance
* **Deadline Driven**: favors urgency

---

## API

### Add Task(s)

`POST /api/tasks/add`

Add one task (form). Validates, stores, returns IDs.

```json
{
    "task": {
        "title": "Fix signup bug",
        "due_date": "2021-12-01",
        "estimated_hours": 1,
        "importance": 4,
        "dependencies": []
  }
}
```

### Analyze BULK JSON Tasks

`POST /api/tasks/analyze?mode=smart`

Returns **all** tasks sorted as per selected mode.

```json
// test data
[
    {
      "id": 1,
      "title": "Release hotfix",
      "due_date": "2025-11-30",
      "estimated_hours": 1,
      "importance": 9,
      "dependencies": [2]
    },
    {
      "id": 2,
      "title": "Fix core bug",
      "due_date": "2024-11-22",
      "estimated_hours": 4,
      "importance": 8,
      "dependencies": [3]
    },
    {
      "id": 3,
      "title": "Refactor auth module",
      "estimated_hours": 6,
      "importance": 7,
      "dependencies": []
    }
  ]
```

### Analyze DB stored task

`GET /api/tasks/analyze_db/?mode=smart`

Returns **all** tasks stored in DB sorted as per selected mode.

### Suggest Today’s Work

`GET /api/tasks/suggest?mode=smart`

Returns **top 3 executable** tasks (depth = 0).

#### Example Response (`/suggest`)

```json
{
  "mode": "smart",
  "warnings": [],
  "top_3": [
    {
      "id": 3,
      "title": "UI polish",
      "due_date": null,
      "effort": 5,
      "importance": 6,
      "priority_score": 0.42,
      "priority_indicator": "Medium",
      "reasons": ["High importance"]
    }
  ]
}
```
--- 

## Output Display (Frontend)

* Color-coded priority: High / Medium / Low
* Shows: title, due date, effort, importance, priority score, flag
* Renders explanation (“reasons”) per task

---

## Setup Instructions

### Requirements

* Python 3.10+
* Django
* SQLite (bundled with Python)

### Install & Run

```bash
git clone https://github.com/gopisekar04/TASK_ANALYZER.git
cd task_analyzer
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # optional (for admin UI)
python manage.py runserver
```

Open: `http://127.0.0.1:8000/`

---

## Testing

Run unit tests:

```bash
python manage.py test
```

Covered:

* Dependency ordering
* Overdue does not beat blockers
* Mode behavior (Fastest Wins)
* Cycle detection

---

## Design Decisions

* **Depth before score**: enforces real executability, not just urgency.
* **Single scoring engine, multiple modes**: flexible behavior without code duplication.
* **Warnings vs errors**: malformed data fails; safe omissions use defaults (with warnings).
* **Cycles are fatal**: an impossible plan should not be ranked.

---

## Phase Plan

### Phase 1 — Intelligence First (No DB)

* Validate input JSON
* Build dependency graph
* Detect cycles
* Score and sort

### Phase 2 — Database Mode (Current)

* Persist tasks
* Analyze/Suggest from DB

---

## Future Improvements

* Visual dependency graphs
* Marking tasks as completed
* Prettify UI
* feature to delete tasks

---

## Dependencies

See `requirements.txt`. Major ones:

* Django
* Python standard library