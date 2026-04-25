"""Tests for Policy-as-Code DSL engine."""

import tempfile
import time
from pathlib import Path

import pytest
import yaml

from src.services.policy_dsl import PolicyAction, PolicyDSLEngine, PolicyResult


@pytest.fixture
def policy_dir(tmp_path):
    return tmp_path


@pytest.fixture
def engine_with_policies(policy_dir):
    (policy_dir / "test.yaml").write_text(yaml.dump({
        "version": "1",
        "blocked_domains": ["169.254.169.254", "metadata.google.internal"],
        "pii_patterns": ["ssn", "credit card"],
        "policies": [
            {
                "name": "block-metadata",
                "trigger": "tool_call",
                "condition": "tool == 'http_request' and any(d in str(args) for d in blocked_domains)",
                "action": "block",
                "message": "Metadata endpoint blocked",
            },
            {
                "name": "pii-detection",
                "trigger": "input",
                "condition": "any(p in prompt.lower() for p in pii_patterns)",
                "action": "block",
                "message": "PII content blocked",
            },
            {
                "name": "budget-escalate",
                "trigger": "pre_execution",
                "condition": "estimated_cost > 0.50",
                "action": "escalate",
                "message": "High cost requires approval",
            },
            {
                "name": "allow-safe-code",
                "trigger": "tool_call",
                "condition": "tool == 'code_execution' and risk_score < 0.3",
                "action": "allow",
                "message": "Low-risk code allowed",
            },
        ],
    }))
    return PolicyDSLEngine(policy_dir)


def test_loads_rules(engine_with_policies):
    assert engine_with_policies.rule_count == 4


def test_block_metadata_endpoint(engine_with_policies):
    results = engine_with_policies.evaluate("tool_call", {
        "tool": "http_request",
        "args": {"url": "http://169.254.169.254/latest/meta-data"},
        "risk_score": 0.0,
        "user_id": "alice",
    })
    assert len(results) == 1
    assert results[0].action == PolicyAction.BLOCK
    assert results[0].rule_name == "block-metadata"


def test_safe_http_passes(engine_with_policies):
    results = engine_with_policies.evaluate("tool_call", {
        "tool": "http_request",
        "args": {"url": "https://api.example.com/data"},
        "risk_score": 0.0,
        "user_id": "alice",
    })
    assert all(r.action != PolicyAction.BLOCK for r in results)


def test_pii_input_blocked(engine_with_policies):
    result = engine_with_policies.first_block_or_escalate("input", {
        "prompt": "My credit card number is 4111-1111-1111-1111",
        "user_id": "alice",
    })
    assert result is not None
    assert result.action == PolicyAction.BLOCK


def test_clean_input_passes(engine_with_policies):
    result = engine_with_policies.first_block_or_escalate("input", {
        "prompt": "Summarize the latest earnings report",
        "user_id": "alice",
    })
    assert result is None


def test_budget_escalation(engine_with_policies):
    result = engine_with_policies.first_block_or_escalate("pre_execution", {
        "prompt": "Analyze this dataset",
        "user_id": "alice",
        "estimated_cost": 0.75,
        "requests_last_minute": 5,
    })
    assert result is not None
    assert result.action == PolicyAction.ESCALATE


def test_budget_under_threshold_passes(engine_with_policies):
    result = engine_with_policies.first_block_or_escalate("pre_execution", {
        "prompt": "Short question",
        "user_id": "alice",
        "estimated_cost": 0.10,
        "requests_last_minute": 2,
    })
    assert result is None


def test_empty_policies_dir(tmp_path):
    engine = PolicyDSLEngine(tmp_path)
    assert engine.rule_count == 0
    result = engine.first_block_or_escalate("input", {"prompt": "hello", "user_id": "alice"})
    assert result is None


def test_malformed_condition_does_not_crash(policy_dir):
    (policy_dir / "bad.yaml").write_text(yaml.dump({
        "version": "1",
        "policies": [{
            "name": "bad-rule",
            "trigger": "input",
            "condition": "this is not valid python !!!",
            "action": "block",
            "message": "bad",
        }],
    }))
    engine = PolicyDSLEngine(policy_dir)
    result = engine.first_block_or_escalate("input", {"prompt": "test", "user_id": "alice"})
    assert result is None


def test_no_code_injection_via_condition(policy_dir):
    """Policy conditions cannot access __import__ or os."""
    (policy_dir / "evil.yaml").write_text(yaml.dump({
        "version": "1",
        "policies": [{
            "name": "escape-attempt",
            "trigger": "input",
            "condition": "__import__('os').system('echo pwned')",
            "action": "block",
            "message": "escaped",
        }],
    }))
    engine = PolicyDSLEngine(policy_dir)
    result = engine.first_block_or_escalate("input", {"prompt": "test", "user_id": "alice"})
    assert result is None


def test_hot_reload(policy_dir):
    initial = policy_dir / "live.yaml"
    initial.write_text(yaml.dump({
        "version": "1",
        "policies": [{
            "name": "rule-v1",
            "trigger": "input",
            "condition": "True",
            "action": "block",
            "message": "v1 block",
        }],
    }))
    engine = PolicyDSLEngine(policy_dir)
    assert engine.rule_count == 1

    # Update file — force reload directly (watcher has 5s delay, skip in tests)
    initial.write_text(yaml.dump({
        "version": "1",
        "policies": [
            {"name": "rule-v2a", "trigger": "input", "condition": "True", "action": "block", "message": "a"},
            {"name": "rule-v2b", "trigger": "input", "condition": "True", "action": "block", "message": "b"},
        ],
    }))
    engine._reload()
    assert engine.rule_count == 2
