from uuid import UUID

from app.investigation.models import InvestigationApprovalDecision


class InvestigationApprovalService:
    def __init__(self, connection, approval_repository):
        self.connection = connection
        self.approval_repository = approval_repository

    def submit_for_approval(
        self,
        investigation_id: int,
        actor_user_id: int,
        comment: str,
        explanation_run_id: UUID | None = None,
    ):
        try:
            event = self.approval_repository.submit_for_approval(
                investigation_id,
                actor_user_id,
                comment,
                explanation_run_id,
            )
            self.connection.commit()
            return event
        except Exception:
            self.connection.rollback()
            raise

    def decide(
        self,
        investigation_id: int,
        actor_user_id: int,
        decision: InvestigationApprovalDecision,
        comment: str,
    ):
        try:
            event = self.approval_repository.decide(
                investigation_id,
                actor_user_id,
                decision,
                comment,
            )
            self.connection.commit()
            return event
        except Exception:
            self.connection.rollback()
            raise

    def list_events(self, investigation_id: int):
        return self.approval_repository.list_events(investigation_id)