from app.ai.models import (
    InvestigationExplanation,
    InvestigationExplanationContext,
)


class DeterministicExplanationProvider:
    name = "deterministic-demo-provider"
    model = "deterministic-v1"

    def explain(
        self,
        context: InvestigationExplanationContext,
    ) -> InvestigationExplanation:
        record = context.investigation
        finding = record.finding

        if finding is None or record.case.investigation_id is None:
            raise ValueError(
                "Investigation does not contain a persisted finding"
            )

        severity = finding.severity.upper()
        discrepancy = f"{record.case.discrepancy:.2f}"
        root_cause_explanations = [
            f"The deterministic investigation classified this cause as {cause}."
            for cause in finding.root_causes
        ]

        summary = (
            f"Investigation {record.case.investigation_id} found a {severity} "
            f"financial discrepancy of {discrepancy} for settlement "
            f"{record.case.settlement_id}."
        )
        business_impact = (
            f"The expected cash differs from actual cash by {discrepancy}. "
            "This finding should be reviewed before settlement reprocessing."
        )

        return InvestigationExplanation(
            investigation_id=record.case.investigation_id,
            summary=summary,
            business_impact=business_impact,
            root_cause_explanations=root_cause_explanations,
            evidence=finding.evidence,
            confidence="HIGH" if finding.evidence else "LOW",
            recommended_action=finding.recommended_action,
            requires_human_review=severity in {"HIGH", "CRITICAL"},
            provider=self.name,
            policy_references=[
                policy.reference
                for policy in context.policy_guidance
            ],
        )
