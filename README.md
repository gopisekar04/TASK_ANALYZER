# Task Analyzer

Task Analyzer is a Django mini-project that takes a list of tasks and decides
what should be done first using an intelligent scoring system.

This project does not just sort tasks.
It reasons about urgency, importance, effort and dependencies and returns the top priorities.

## What this project does

Each task has:

- id
- Title
- Due date
- Estimated hours
- Importance (1–10)
- Dependencies (tasks that must be done first)

The system calculates a priority score for every task based on:

- How close the deadline is
- How important the task is
- How small or large the task is
- Whether the task blocks other tasks
- Whether the task itself is blocked

Then it:

- Sorts tasks by priority
- Returns the top 3 tasks to focus on
- Explains why they are important

## Development Approach

## Phase 1 — Intelligence First (No Database)

First, the algorithm is built to:

- Accept a list of tasks as JSON
- Compute a score for each task
- Sort and suggest the best tasks

No database is required for this stage as to understand what data is actually needed before actually determining the model rather than adjusting often later. Also scoring algorithm is determins the schema not the other way around.

## step 1 - Receive data and validate
The request is received in tasks/views.py

- check if "tasks" exists if empty list return `"message": "Empty list"`
- check that each task has required fields and respective data type
- Handle missing values - using default values if safe to use eg. importance = 5 (medium), dependencies = [] (empty list)
- Cruial fields such as title, due_date, estimated_hours - if missing return `"error": "Missing required fields"` 

## step 2 - Construct dependency list
- Which task depends on whom
- which task blocks others

## step 3 - Detect circular dependencies
- If cycle is detected `"error": "Circualar dependency detected"`
- else continue

## step 4 - Compute dependency score
- The priority_score is a cumulative based on 4 different scores given to each task
### i. urgency_score

| condition | Score|
| :--- | :--- |
| Overdue | 1.00 |
| Today | 0.95 |
| Tomorrow | 0.85 |
| 2-3 days | 0.65 |
| 4-7 days | 0.40 |
| 8-14 dasys | 0.20 |
| >14 days | 0.10 |

### ii. Importance score
Normalize the user provided imprtance
`importance_score = importance / 10`

### iii. Effort Score
Lower efforts receive higher score

| Hours | Score |
| :--- | :--- |
| <=1 | 1.00 |
| 2-4 | 0.70 |
| 5-8 | 0.40 |
| >8 | 0.20 |

### Dependency Score

| No. of dependents | Score |
| :--- | :--- |
| 0 | 0.00 | 
| 1 | 0.40 |
| 2 | 0.70 |
| >3 | 1.00 |

### Final Score Formula
Weight for each score
| Score | weight % |
| :--- | :--- |
| urgency_score | 40% |
| importance_score | 25% |
| dependency_score | 20% |
| effor_score | 15% |

`priority_score = (urgency_score * 0.40) + (importance_score * 0.25) + (dependency_score * 0.20) + (effor_score * 0.15)`

## Find depth of each task
The depth of each task lets us sort the tasks ensuring no blocked tasks floats above its dependencies.

## Sorting based on depth and priority_score