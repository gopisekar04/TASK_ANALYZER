from django.test import TestCase
from .scoring import score_tasks, validate_tasks
from .views import build_graph, detect_cycle, CycleError


class ScoringAlgorithmTests(TestCase):

    def test_dependency_order_is_respected(self):
        """
        A task must NEVER appear before its dependency.
        """

        tasks = [
            {"id": 1, "title": "Deploy", "estimated_hours": 1, "importance": 9, "dependencies": [2]},
            {"id": 2, "title": "Fix bug", "estimated_hours": 2, "importance": 8, "dependencies": [3]},
            {"id": 3, "title": "Refactor", "estimated_hours": 3, "importance": 7, "dependencies": []},
        ]

        tasks, _ = validate_tasks(tasks)
        graph = build_graph(tasks)
        detect_cycle(graph)

        ranked = score_tasks(tasks, graph, mode="smart")

        ids = [t["id"] for t in ranked]

        # Dependency order must hold: 3 → 2 → 1
        self.assertTrue(ids.index(3) < ids.index(2) < ids.index(1))


    def test_overdue_task_not_ranked_above_dependency(self):
        """
        Even if overdue, a blocked task must not outrank its blocker.
        """

        tasks = [
            {"id": 1, "title": "Release", "due_date": "2024-01-01", "estimated_hours": 1, "importance": 10, "dependencies": [2]},
            {"id": 2, "title": "Build", "estimated_hours": 4, "importance": 5, "dependencies": []}
        ]

        tasks, _ = validate_tasks(tasks)
        graph = build_graph(tasks)
        detect_cycle(graph)

        ranked = score_tasks(tasks, graph, mode="deadline")

        self.assertEqual(ranked[0]["id"], 2)  # Builder must come before overdue Release


    def test_fastest_mode_prioritizes_low_effort(self):
        """
        Fastest-wins mode must push quick tasks to the top.
        """

        tasks = [
            {"id": 1, "title": "Big Task", "estimated_hours": 10, "importance": 10, "dependencies": []},
            {"id": 2, "title": "Quick Fix", "estimated_hours": 1, "importance": 3, "dependencies": []}
        ]

        tasks, _ = validate_tasks(tasks)
        graph = build_graph(tasks)
        detect_cycle(graph)

        ranked = score_tasks(tasks, graph, mode="fastest")

        self.assertEqual(ranked[0]["title"], "Quick Fix")


class DependencyValidationTests(TestCase):

    def test_cycle_detection(self):
        """
        Circular dependencies must raise error.
        """

        tasks = [
            {"id": 1, "title": "A", "estimated_hours": 1, "importance": 5, "dependencies": [2]},
            {"id": 2, "title": "B", "estimated_hours": 1, "importance": 5, "dependencies": [1]},
        ]

        tasks, _ = validate_tasks(tasks)
        graph = build_graph(tasks)

        with self.assertRaises(Exception):
            detect_cycle(graph)
