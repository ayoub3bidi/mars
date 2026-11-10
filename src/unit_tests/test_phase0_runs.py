from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from routes.runs import create_run
from schemas.Run import RunCreate


class Query:
    def __init__(self, run):
        self.run = run

    def filter(self, _expression):
        return self

    def first(self):
        return self.run


class Database:
    def __init__(self, run=None):
        self.run = run
        self.added = None

    def query(self, _model):
        return Query(self.run)

    def add(self, run):
        self.added = run

    def commit(self):
        self.added.id = uuid4()
        self.added.created_at = datetime.now(timezone.utc)
        self.added.updated_at = self.added.created_at
        self.run = self.added

    def refresh(self, _run):
        return None


def test_run_creation_queues_task_and_returns_record(monkeypatch):
    db = Database()
    queue = Mock()
    monkeypatch.setattr("routes.runs.execute_run.delay", queue)

    run = create_run(RunCreate(prompt="  explain Mars  "), db, "request-1")

    assert run.prompt == "explain Mars"
    assert run.status == "queued"
    queue.assert_called_once_with(str(run.id))


def test_reusing_idempotency_key_for_different_prompt_returns_conflict():
    run = Mock(prompt="original")
    db = Database(run)

    with pytest.raises(HTTPException) as error:
        create_run(RunCreate(prompt="different"), db, "request-1")

    assert error.value.status_code == 409


@pytest.mark.parametrize("token_budget", [0, 257])
def test_invalid_token_budget_is_rejected(token_budget):
    with pytest.raises(HTTPException) as error:
        create_run(RunCreate(prompt="prompt", token_budget=token_budget), Database(), None)
    assert error.value.status_code == 400
