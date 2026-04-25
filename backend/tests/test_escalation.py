"""Tests for human-in-the-loop escalation service."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database import Base
from src.services.escalation import EscalationService, EscalationStatus


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _create(db, user_id="alice", trigger_type="policy_rule", trigger_name="budget-escalate",
            risk_score=0.7, message="High cost"):
    svc = EscalationService(db)
    return svc.create(
        user_id=user_id,
        trigger_type=trigger_type,
        trigger_name=trigger_name,
        context={"prompt": "analyze this", "estimated_cost": 0.75},
        risk_score=risk_score,
        policy_message=message,
    )


def test_create_returns_pending_item(db):
    item = _create(db)
    assert item.status == EscalationStatus.PENDING
    assert item.user_id == "alice"
    assert item.trigger_name == "budget-escalate"
    assert item.risk_score == 0.7


def test_get_by_id(db):
    created = _create(db)
    svc = EscalationService(db)
    fetched = svc.get(int(created.id))
    assert fetched is not None
    assert fetched.id == created.id


def test_get_nonexistent_returns_none(db):
    svc = EscalationService(db)
    assert svc.get(99999) is None


def test_approve(db):
    item = _create(db)
    svc = EscalationService(db)
    decided = svc.decide(int(item.id), approved=True, decided_by="ops_team", comment="Looks fine")
    assert decided.status == EscalationStatus.APPROVED
    assert decided.decided_by == "ops_team"


def test_deny(db):
    item = _create(db)
    svc = EscalationService(db)
    decided = svc.decide(int(item.id), approved=False, decided_by="security", comment="Too risky")
    assert decided.status == EscalationStatus.DENIED


def test_double_decide_returns_none(db):
    item = _create(db)
    svc = EscalationService(db)
    svc.decide(int(item.id), approved=True, decided_by="admin")
    second = svc.decide(int(item.id), approved=False, decided_by="admin")
    assert second is None


def test_list_pending_only_shows_pending(db):
    svc = EscalationService(db)
    i1 = _create(db, user_id="alice")
    i2 = _create(db, user_id="bob")
    svc.decide(int(i1.id), approved=True, decided_by="admin")

    pending = svc.list_pending()
    ids = [p.id for p in pending]
    assert i2.id in ids
    assert i1.id not in ids


def test_list_all_includes_decided(db):
    svc = EscalationService(db)
    i1 = _create(db)
    svc.decide(int(i1.id), approved=True, decided_by="admin")
    _create(db, user_id="bob")

    all_items = svc.list_all()
    assert len(all_items) == 2


def test_timeout_deny_by_default(db, monkeypatch):
    import os
    monkeypatch.setenv("ESCALATION_TIMEOUT_SECONDS", "0")
    monkeypatch.setenv("ESCALATION_TIMEOUT_ACTION", "deny")
    item = _create(db)
    svc = EscalationService(db)
    fetched = svc.get(int(item.id))
    assert fetched.status == EscalationStatus.DENIED


def test_timeout_approve_when_configured(db, monkeypatch):
    monkeypatch.setenv("ESCALATION_TIMEOUT_SECONDS", "0")
    monkeypatch.setenv("ESCALATION_TIMEOUT_ACTION", "approve")
    item = _create(db)
    svc = EscalationService(db)
    fetched = svc.get(int(item.id))
    assert fetched.status == EscalationStatus.APPROVED


def test_context_preserved(db):
    svc = EscalationService(db)
    item = svc.create(
        user_id="alice",
        trigger_type="tool_call",
        trigger_name="high-risk-tool-escalate",
        context={"tool": "code_execution", "args": {"code": "print('hi')"}},
        risk_score=0.8,
        policy_message="Requires review",
    )
    fetched = svc.get(int(item.id))
    assert fetched.context["tool"] == "code_execution"
    assert fetched.risk_score == 0.8
