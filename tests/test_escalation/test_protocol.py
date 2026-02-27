"""Tests for agent_sense.escalation.protocol — EscalationProtocol."""
from __future__ import annotations

import pytest

from agent_sense.escalation.protocol import (
    EscalationLevel,
    EscalationProtocol,
    EscalationRecord,
    EscalationTrigger,
    EscalationTriggerConfig,
)


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


class TestEscalationProtocolInitialState:
    def test_default_level_is_agent(self) -> None:
        protocol = EscalationProtocol()
        assert protocol.current_level == EscalationLevel.AGENT

    def test_not_escalated_initially(self) -> None:
        protocol = EscalationProtocol()
        assert protocol.is_escalated is False

    def test_empty_history(self) -> None:
        protocol = EscalationProtocol()
        assert protocol.history == []


# ---------------------------------------------------------------------------
# LOW_CONFIDENCE trigger
# ---------------------------------------------------------------------------


class TestLowConfidenceTrigger:
    def test_fires_when_below_threshold(self) -> None:
        protocol = EscalationProtocol()
        record = protocol.evaluate(confidence_score=0.20)
        assert record is not None
        assert record.trigger == EscalationTrigger.LOW_CONFIDENCE

    def test_does_not_fire_at_threshold(self) -> None:
        protocol = EscalationProtocol()
        record = protocol.evaluate(confidence_score=0.40)
        assert record is None

    def test_does_not_fire_above_threshold(self) -> None:
        protocol = EscalationProtocol()
        record = protocol.evaluate(confidence_score=0.75)
        assert record is None

    def test_escalates_to_supervisor_by_default(self) -> None:
        protocol = EscalationProtocol()
        record = protocol.evaluate(confidence_score=0.10)
        assert record is not None
        assert record.to_level == EscalationLevel.SUPERVISOR

    def test_updates_current_level(self) -> None:
        protocol = EscalationProtocol()
        protocol.evaluate(confidence_score=0.10)
        assert protocol.current_level == EscalationLevel.SUPERVISOR
        assert protocol.is_escalated is True


# ---------------------------------------------------------------------------
# HIGH_RISK trigger
# ---------------------------------------------------------------------------


class TestHighRiskTrigger:
    def test_fires_when_high_risk_true(self) -> None:
        protocol = EscalationProtocol()
        record = protocol.evaluate(high_risk=True)
        assert record is not None
        assert record.trigger == EscalationTrigger.HIGH_RISK

    def test_does_not_fire_when_false(self) -> None:
        protocol = EscalationProtocol()
        record = protocol.evaluate(high_risk=False)
        assert record is None

    def test_escalates_to_human(self) -> None:
        protocol = EscalationProtocol()
        record = protocol.evaluate(high_risk=True)
        assert record is not None
        assert record.to_level == EscalationLevel.HUMAN


# ---------------------------------------------------------------------------
# USER_REQUESTED trigger
# ---------------------------------------------------------------------------


class TestUserRequestedTrigger:
    def test_fires_when_requested(self) -> None:
        protocol = EscalationProtocol()
        record = protocol.evaluate(user_requested=True)
        assert record is not None
        assert record.trigger == EscalationTrigger.USER_REQUESTED

    def test_escalates_to_human(self) -> None:
        protocol = EscalationProtocol()
        record = protocol.evaluate(user_requested=True)
        assert record is not None
        assert record.to_level == EscalationLevel.HUMAN


# ---------------------------------------------------------------------------
# POLICY_VIOLATION trigger
# ---------------------------------------------------------------------------


class TestPolicyViolationTrigger:
    def test_fires_on_violation(self) -> None:
        protocol = EscalationProtocol()
        record = protocol.evaluate(policy_violation=True)
        assert record is not None
        assert record.trigger == EscalationTrigger.POLICY_VIOLATION

    def test_policy_violation_has_priority_over_low_confidence(self) -> None:
        protocol = EscalationProtocol()
        record = protocol.evaluate(confidence_score=0.10, policy_violation=True)
        assert record is not None
        assert record.trigger == EscalationTrigger.POLICY_VIOLATION


# ---------------------------------------------------------------------------
# REPEATED_FAILURE trigger
# ---------------------------------------------------------------------------


class TestRepeatedFailureTrigger:
    def test_fires_at_threshold(self) -> None:
        protocol = EscalationProtocol()
        # Default threshold is 3
        record = protocol.evaluate(failure_count=3)
        assert record is not None
        assert record.trigger == EscalationTrigger.REPEATED_FAILURE

    def test_fires_above_threshold(self) -> None:
        protocol = EscalationProtocol()
        record = protocol.evaluate(failure_count=5)
        assert record is not None

    def test_does_not_fire_below_threshold(self) -> None:
        protocol = EscalationProtocol()
        record = protocol.evaluate(failure_count=2)
        assert record is None

    def test_zero_failures_no_fire(self) -> None:
        protocol = EscalationProtocol()
        record = protocol.evaluate(failure_count=0)
        assert record is None


# ---------------------------------------------------------------------------
# TIMEOUT trigger
# ---------------------------------------------------------------------------


class TestTimeoutTrigger:
    def test_fires_on_timeout(self) -> None:
        protocol = EscalationProtocol()
        record = protocol.evaluate(timeout=True)
        assert record is not None
        assert record.trigger == EscalationTrigger.TIMEOUT


# ---------------------------------------------------------------------------
# EscalationRecord properties
# ---------------------------------------------------------------------------


class TestEscalationRecord:
    def test_record_has_unique_ids(self) -> None:
        protocol = EscalationProtocol()
        r1 = protocol.evaluate(high_risk=True)
        protocol2 = EscalationProtocol()
        r2 = protocol2.evaluate(high_risk=True)
        assert r1 is not None and r2 is not None
        assert r1.escalation_id != r2.escalation_id

    def test_record_from_level(self) -> None:
        protocol = EscalationProtocol()
        record = protocol.evaluate(high_risk=True)
        assert record is not None
        assert record.from_level == EscalationLevel.AGENT

    def test_record_reason_default(self) -> None:
        protocol = EscalationProtocol()
        record = protocol.evaluate(high_risk=True)
        assert record is not None
        assert len(record.reason) > 0

    def test_record_reason_override(self) -> None:
        protocol = EscalationProtocol()
        record = protocol.evaluate(high_risk=True, reason="Custom reason")
        assert record is not None
        assert record.reason == "Custom reason"

    def test_record_metadata(self) -> None:
        protocol = EscalationProtocol()
        record = protocol.evaluate(high_risk=True, metadata={"source": "policy-engine"})
        assert record is not None
        assert record.metadata["source"] == "policy-engine"

    def test_record_to_dict(self) -> None:
        protocol = EscalationProtocol()
        record = protocol.evaluate(high_risk=True)
        assert record is not None
        d = record.to_dict()
        assert "escalation_id" in d
        assert "from_level" in d
        assert "to_level" in d
        assert "trigger" in d
        assert d["trigger"] == "high_risk"


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


class TestEscalationHistory:
    def test_history_accumulates(self) -> None:
        protocol = EscalationProtocol()
        protocol.evaluate(high_risk=True)
        # After escalation, further evaluate does not fire more triggers on
        # same protocol instance unless conditions change — test manual sequence
        assert len(protocol.history) == 1

    def test_history_is_copy(self) -> None:
        protocol = EscalationProtocol()
        protocol.evaluate(high_risk=True)
        history = protocol.history
        history.clear()  # modifying the copy
        assert len(protocol.history) == 1


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


class TestReset:
    def test_reset_clears_level(self) -> None:
        protocol = EscalationProtocol()
        protocol.evaluate(high_risk=True)
        assert protocol.current_level == EscalationLevel.HUMAN
        protocol.reset()
        assert protocol.current_level == EscalationLevel.AGENT

    def test_reset_clears_history(self) -> None:
        protocol = EscalationProtocol()
        protocol.evaluate(high_risk=True)
        protocol.reset()
        assert protocol.history == []

    def test_reset_to_custom_level(self) -> None:
        protocol = EscalationProtocol()
        protocol.evaluate(high_risk=True)
        protocol.reset(level=EscalationLevel.SUPERVISOR)
        assert protocol.current_level == EscalationLevel.SUPERVISOR


# ---------------------------------------------------------------------------
# Custom trigger config
# ---------------------------------------------------------------------------


class TestCustomTriggerConfig:
    def test_disabled_trigger_does_not_fire(self) -> None:
        configs = [
            EscalationTriggerConfig(
                trigger=EscalationTrigger.LOW_CONFIDENCE,
                enabled=False,
                threshold=0.40,
                target_level=EscalationLevel.SUPERVISOR,
            )
        ]
        protocol = EscalationProtocol(trigger_configs=configs)
        record = protocol.evaluate(confidence_score=0.0)
        assert record is None

    def test_custom_threshold(self) -> None:
        configs = [
            EscalationTriggerConfig(
                trigger=EscalationTrigger.LOW_CONFIDENCE,
                enabled=True,
                threshold=0.80,
                target_level=EscalationLevel.SUPERVISOR,
            )
        ]
        protocol = EscalationProtocol(trigger_configs=configs)
        record = protocol.evaluate(confidence_score=0.75)
        assert record is not None
        assert record.trigger == EscalationTrigger.LOW_CONFIDENCE

    def test_custom_target_level(self) -> None:
        configs = [
            EscalationTriggerConfig(
                trigger=EscalationTrigger.HIGH_RISK,
                enabled=True,
                threshold=0.0,
                target_level=EscalationLevel.SUPERVISOR,
            )
        ]
        protocol = EscalationProtocol(trigger_configs=configs)
        record = protocol.evaluate(high_risk=True)
        assert record is not None
        assert record.to_level == EscalationLevel.SUPERVISOR
