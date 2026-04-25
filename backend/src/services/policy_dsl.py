"""Policy-as-Code engine: loads YAML policy files, evaluates rules against request context."""

import logging
import os
import threading
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

POLICIES_DIR = Path(__file__).parent.parent.parent / "policies"

# Safe builtins available in policy condition expressions
_SAFE_BUILTINS = {
    "any": any,
    "all": all,
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "isinstance": isinstance,
    "bool": bool,
}


class PolicyAction(str, Enum):
    BLOCK = "block"
    ESCALATE = "escalate"
    ALLOW = "allow"


@dataclass
class PolicyRule:
    name: str
    trigger: str
    condition: str
    action: PolicyAction
    message: str


@dataclass
class PolicyResult:
    rule_name: str
    action: PolicyAction
    message: str
    matched: bool = True


class PolicyDSLEngine:
    """
    Loads policy YAML files from the policies directory and evaluates
    rules against a context dict using safe expression evaluation.
    Watches for file changes and hot-reloads without restart.
    """

    def __init__(self, policies_dir: Path = POLICIES_DIR):
        self._dir = policies_dir
        self._rules: list[PolicyRule] = []
        self._meta: dict[str, Any] = {}
        self._lock = threading.RLock()
        self._last_mtime: dict[str, float] = {}
        self._reload()
        self._start_watcher()

    def _reload(self) -> None:
        rules: list[PolicyRule] = []
        meta: dict[str, Any] = {}

        if not self._dir.exists():
            logger.warning("Policies directory not found: %s", self._dir)
            with self._lock:
                self._rules = rules
                self._meta = meta
            return

        for path in sorted(self._dir.glob("*.yaml")):
            try:
                with open(path) as f:
                    doc = yaml.safe_load(f)
                if not doc:
                    continue

                # Collect top-level metadata (blocked_domains, pii_patterns, etc.)
                for k, v in doc.items():
                    if k != "policies" and k != "version":
                        meta[k] = v

                for rule_def in doc.get("policies", []):
                    rules.append(PolicyRule(
                        name=rule_def["name"],
                        trigger=rule_def["trigger"],
                        condition=rule_def["condition"],
                        action=PolicyAction(rule_def["action"]),
                        message=rule_def.get("message", rule_def["name"]),
                    ))

                self._last_mtime[str(path)] = path.stat().st_mtime
                logger.info("Loaded policy file: %s (%d rules)", path.name, len(doc.get("policies", [])))
            except Exception as e:
                logger.error("Failed to load policy file %s: %s", path, e)

        with self._lock:
            self._rules = rules
            self._meta = meta

    def _start_watcher(self) -> None:
        def watch():
            while True:
                time.sleep(5)
                try:
                    changed = False
                    for path in self._dir.glob("*.yaml"):
                        mtime = path.stat().st_mtime
                        if self._last_mtime.get(str(path)) != mtime:
                            changed = True
                            break
                    if changed:
                        logger.info("Policy files changed — reloading")
                        self._reload()
                except Exception as e:
                    logger.error("Policy watcher error: %s", e)

        t = threading.Thread(target=watch, daemon=True)
        t.start()

    def evaluate(self, trigger: str, context: dict[str, Any]) -> list[PolicyResult]:
        """
        Evaluate all rules matching the given trigger against context.
        Returns list of PolicyResult for any rules that matched.
        context keys vary by trigger:
          input:         prompt, user_id
          pre_execution: prompt, user_id, estimated_cost, requests_last_minute
          tool_call:     tool, args, risk_score, user_id
        """
        with self._lock:
            rules = [r for r in self._rules if r.trigger == trigger]
            # Everything goes into globals so generator expressions inside conditions can see them.
            # __builtins__ set to {} to block os, open, __import__, etc.
            eval_ns: dict[str, Any] = {"__builtins__": {}}
            eval_ns.update(_SAFE_BUILTINS)
            eval_ns.update(self._meta)
            eval_ns.update(context)

        results: list[PolicyResult] = []
        for rule in rules:
            try:
                matched = bool(eval(rule.condition, eval_ns))  # noqa: S307
            except Exception as e:
                logger.warning("Policy rule '%s' condition error: %s", rule.name, e)
                matched = False

            if matched:
                results.append(PolicyResult(
                    rule_name=rule.name,
                    action=rule.action,
                    message=rule.message,
                ))

        return results

    def first_block_or_escalate(self, trigger: str, context: dict[str, Any]) -> PolicyResult | None:
        """Return the first blocking or escalating rule match, or None if all pass."""
        results = self.evaluate(trigger, context)
        for r in results:
            if r.action in (PolicyAction.BLOCK, PolicyAction.ESCALATE):
                return r
        return None

    @property
    def rule_count(self) -> int:
        with self._lock:
            return len(self._rules)


# Module-level singleton — imported by policy service
_engine: PolicyDSLEngine | None = None


def get_policy_engine() -> PolicyDSLEngine:
    global _engine
    if _engine is None:
        _engine = PolicyDSLEngine()
    return _engine
