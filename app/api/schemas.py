from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.investigation.models import InvestigationApprovalDecision

class InvestigationFindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    root_causes: list[str]
    impact: str
    severity: str
    evidence: list[str]
    recommended_action: str | None


class InvestigationExplanationResponse(BaseModel):
    investigation_id: int
    summary: str
    business_impact: str
    root_cause_explanations: list[str]
    evidence: list[str]
    confidence: str
    recommended_action: str | None
    requires_human_review: bool
    provider: str
    preventive_actions: list[str]
    policy_references: list[str]
    audit_run_id: UUID | None


class SubmitForApprovalRequest(BaseModel):
    comment: str = Field(min_length=3, max_length=1000)
    explanation_run_id: UUID | None = None

    @field_validator("comment")
    @classmethod
    def comment_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Comment cannot be blank")
        return value


class InvestigationApprovalDecisionRequest(BaseModel):
    decision: InvestigationApprovalDecision
    comment: str = Field(min_length=3, max_length=1000)

    @field_validator("comment")
    @classmethod
    def comment_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Comment cannot be blank")
        return value


class InvestigationApprovalEventResponse(BaseModel):
    approval_event_id: int
    investigation_id: int
    actor_user_id: int
    explanation_run_id: UUID | None
    event_type: str
    previous_status: str
    new_status: str
    comment: str
    created_at: datetime


class InvestigationRecordResponse(BaseModel):
    investigation_id: int
    settlement_id: int
    expected_cash: str
    actual_cash: str
    discrepancy: str
    status: str
    created_at: datetime
    updated_at: datetime
    finding: InvestigationFindingResponse | None


class InvestigationSummaryResponse(BaseModel):
    investigation_id: int
    settlement_id: int
    investigation_type: str
    status: str
    discrepancy: str
    severity: str | None
    created_at: datetime


class InvestigationRunRequest(BaseModel):
    investigation_type: str = Field(
        default="CASH_DISCREPANCY",
        min_length=1,
        max_length=50
    )
    idempotency_key: str = Field(
        min_length=1,
        max_length=100,
    )


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=12, max_length=128)
    role: str = Field(min_length=1, max_length=20)


class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    role: str
    is_active: bool

