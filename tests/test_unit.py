# Unit tests for the deterministic core - no API calls, no network, no cost.
import pytest
from pydantic import ValidationError

from schemas import Plan, Review, Subtask, execution_order
from tools import _safe_path, calculator
from memory import score_similarity


def make_plan(*subtasks):
    return Plan(goal="test", subtasks=list(subtasks))


class TestExecutionOrder:
    def test_linear_chain(self):
        plan = make_plan(
            Subtask(id=1, description="a", specialist="researcher"),
            Subtask(id=2, description="b", specialist="analyst", depends_on=[1]),
            Subtask(id=3, description="c", specialist="writer", depends_on=[2]))
        assert execution_order(plan) == [[1], [2], [3]]

    def test_parallel_wave(self):
        plan = make_plan(
            Subtask(id=1, description="a", specialist="researcher"),
            Subtask(id=2, description="b", specialist="researcher"),
            Subtask(id=3, description="c", specialist="writer", depends_on=[1, 2]))
        assert execution_order(plan) == [[1, 2], [3]]

    def test_missing_dependency_rejected(self):
        plan = make_plan(
            Subtask(id=1, description="a", specialist="writer", depends_on=[99]))
        with pytest.raises(ValueError, match="does not exist"):
            execution_order(plan)

    def test_self_dependency_rejected(self):
        plan = make_plan(
            Subtask(id=1, description="a", specialist="writer", depends_on=[1]))
        with pytest.raises(ValueError, match="depends on itself"):
            execution_order(plan)

    def test_cycle_detected(self):
        plan = make_plan(
            Subtask(id=1, description="a", specialist="researcher", depends_on=[3]),
            Subtask(id=2, description="b", specialist="analyst", depends_on=[1]),
            Subtask(id=3, description="c", specialist="writer", depends_on=[2]))
        with pytest.raises(ValueError, match="cycle"):
            execution_order(plan)


class TestSchemas:
    def test_invalid_specialist_rejected(self):
        with pytest.raises(ValidationError):
            Subtask(id=1, description="a", specialist="accountant")

    def test_review_score_bounds(self):
        with pytest.raises(ValidationError):
            Review(verdict="approve", score=9, feedback="x")
        with pytest.raises(ValidationError):
            Review(verdict="maybe", score=3, feedback="x")


class TestSandbox:
    def test_normal_filename_allowed(self):
        assert _safe_path("notes.txt").name == "notes.txt"

    def test_path_traversal_rejected(self):
        with pytest.raises(ValueError, match="outside workspace"):
            _safe_path("../secrets.txt")

    def test_deep_traversal_rejected(self):
        with pytest.raises(ValueError, match="outside workspace"):
            _safe_path("a/../../.env")


class TestCalculator:
    def test_basic_arithmetic(self):
        assert calculator("2 + 3 * 4") == "14"

    def test_power_operator_blocked(self):
        assert "Error" in calculator("9**9")

    def test_code_injection_blocked(self):
        assert "Error" in calculator("__import__('os')")

    def test_overlong_expression_blocked(self):
        assert "Error" in calculator("1+" * 60 + "1")


class TestMemorySimilarity:
    def test_identical_texts_score_high(self):
        assert score_similarity("invoice GST total", "invoice GST total") == 1.0

    def test_disjoint_texts_score_zero(self):
        assert score_similarity("invoice GST total", "weather forecast delhi") == 0.0

    def test_known_morphology_gap(self):
        # Documents the limitation found in practice: exact-token matching
        # cannot connect 'calculation' with 'calculate'.
        assert score_similarity("calculation", "calculate") == 0.0


class TestStateRoundTrip:
    def test_save_and_load(self, tmp_path, monkeypatch):
        import state
        monkeypatch.setattr(state, "DB_PATH", str(tmp_path / "test.db"))

        task_id = state.create_task("test task")
        plan = make_plan(
            Subtask(id=1, description="a", specialist="researcher"),
            Subtask(id=2, description="b", specialist="writer", depends_on=[1]))
        state.save_plan(task_id, plan)
        state.save_result(task_id, 1, "result one")

        task, status, loaded_plan, results = state.load_task(task_id)
        assert task == "test task"
        assert status == "running"
        assert loaded_plan == plan
        assert results == {1: "result one"}  # int keys survive the JSON round trip

    def test_approval_round_trip(self, tmp_path, monkeypatch):
        import state
        monkeypatch.setattr(state, "DB_PATH", str(tmp_path / "test.db"))

        task_id = state.create_task("test task")
        state.create_approval(task_id, 2, "write something sensitive")
        assert state.get_approval_status(task_id, 2) == "pending"

        pending = state.list_pending_approvals()
        assert len(pending) == 1
        aid = pending[0][0]

        returned_task_id = state.resolve_approval(aid, "approved")
        assert returned_task_id == task_id
        assert state.get_approval_status(task_id, 2) == "approved"
        assert state.list_pending_approvals() == []
