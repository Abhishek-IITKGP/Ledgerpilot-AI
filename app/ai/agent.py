import hashlib
import json
import logging
import re
import time
from dataclasses import asdict
from datetime import datetime, timezone

from app.ai.llm_provider import LLMProviderUnavailableError
from app.ai.models import (
    InvestigationExplanationContext,
)


logger = logging.getLogger(__name__)
PROMPT_VERSION = "investigation-explanation-v1"


class InvestigationExplanationAgent:
    """Gather approved read-only facts, then ask a provider to explain them."""

    def __init__(self, tools, provider, audit_repository):
        self.tools = tools
        self.provider = provider
        self.audit_repository = audit_repository

    def explain_investigation(
        self,
        investigation_id: int,
        requested_by_user_id: int,
    ):
        started_at = datetime.now(timezone.utc)
        start_time = time.perf_counter()
        investigation = self.tools.read_investigation(investigation_id)

        if investigation is None:
            return None

        settlement = self.tools.read_settlement(
            investigation.case.settlement_id
        )
        transaction = self.tools.read_transaction(settlement.transaction_id)
        order = self.tools.read_order(transaction.order_id)
        executions = self.tools.read_executions(order.order_id)
        cash_movements = self.tools.read_cash_movements(
            settlement.settlement_id
        )
        policy_search_terms = self._policy_search_terms(
            investigation,
            settlement.failure_reason,
        )
        policy_guidance = self.tools.read_approved_policies(
            policy_search_terms
        )
        context = InvestigationExplanationContext(
            investigation=investigation,
            settlement=settlement,
            transaction=transaction,
            order=order,
            executions=executions,
            cash_movements=cash_movements,
            policy_guidance=policy_guidance,
        )

        input_snapshot = context.to_prompt_data()
        canonical_input = json.dumps(
            input_snapshot,
            sort_keys=True,
            separators=(",", ":"),
        )
        input_sha256 = hashlib.sha256(
            canonical_input.encode("utf-8")
        ).hexdigest()
        provider_name = self.provider.name
        model = getattr(self.provider, "model", "unspecified")

        try:
            explanation = self.provider.explain(context)
        except Exception as provider_error:
            try:
                self.audit_repository.record_run(
                    investigation_id=investigation_id,
                    requested_by_user_id=requested_by_user_id,
                    provider=provider_name,
                    model=model,
                    prompt_version=PROMPT_VERSION,
                    status="FAILED",
                    input_snapshot=input_snapshot,
                    input_sha256=input_sha256,
                    started_at=started_at,
                    duration_ms=int(
                        (time.perf_counter() - start_time) * 1000
                    ),
                    error_category=self._error_category(provider_error),
                )
            except Exception:
                logger.exception(
                    "Failed to persist AI audit record for "
                    "investigation_id=%s",
                    investigation_id,
                )
            raise provider_error

        audit_run_id = self.audit_repository.record_run(
            investigation_id=investigation_id,
            requested_by_user_id=requested_by_user_id,
            provider=provider_name,
            model=model,
            prompt_version=PROMPT_VERSION,
            status="SUCCEEDED",
            input_snapshot=input_snapshot,
            input_sha256=input_sha256,
            started_at=started_at,
            duration_ms=int((time.perf_counter() - start_time) * 1000),
            output_snapshot=asdict(explanation),
        )
        explanation.audit_run_id = audit_run_id
        return explanation

    @staticmethod
    def _policy_search_terms(investigation, failure_reason: str | None) -> list[str]:
        finding = investigation.finding
        values = list(finding.root_causes) if finding is not None else []
        if failure_reason:
            values.append(failure_reason)

        return sorted(
            {
                term
                for value in values
                for term in re.findall(r"[a-z0-9]+", value.lower())
                if len(term) > 2
            }
        )

    @staticmethod
    def _error_category(error: Exception) -> str:
        if isinstance(error, LLMProviderUnavailableError):
            return "PROVIDER_UNAVAILABLE"
        if isinstance(error, ValueError):
            return "INVALID_PROVIDER_RESPONSE"
        return "AGENT_EXECUTION_ERROR"