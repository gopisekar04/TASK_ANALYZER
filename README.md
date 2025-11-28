# Task Analyzer

Task Analyzer is a Django mini-project that takes a list of tasks and decides
what should be done first using an intelligent scoring system.

This project does not just sort tasks.
It reasons about urgency, importance, effort and dependencies and returns the top priorities.

## What this project does

Each task has:

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

Phase 1 — Intelligence First (No Database)

First, the algorithm is built to:

- Accept a list of tasks as JSON
- Compute a score for each task
- Sort and suggest the best tasks

No database is required for this stage as to understand what data is actually needed before actually determining the model and later adjusting often. Also scoring algorithm is determins the schema not the other way around.

