from uuid import UUID

from app.investigation.approval_errors import (
    ApprovalWorkflowConflict,
    InvestigationNotFoundError,
)
from app.investigation.models import (
    InvestigationApprovalDecision,
    InvestigationApprovalEvent,
)


class InvestigationApprovalRepository:
    def __init__(self, connection):
        self.connection = connection

    def submit_for_approval(
        self,
        investigation_id: int,
        actor_user_id: int,
        comment: str,
        explanation_run_id: UUID | None,
    ) -> InvestigationApprovalEvent:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT status
                FROM investigation.cases
                WHERE investigation_id = %s
                FOR UPDATE
                """,
                (investigation_id,),
            )
            case_row = cursor.fetchone()
            if case_row is None:
                raise InvestigationNotFoundError

            previous_status = case_row[0]
            if previous_status not in {"OPEN", "INVESTIGATING"}:
                raise ApprovalWorkflowConflict(
                    "Only open or investigating cases can be submitted"
                )

            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM investigation.findings
                    WHERE investigation_id = %s
                )
                """,
                (investigation_id,),
            )
            if not cursor.fetchone()[0]:
                raise ApprovalWorkflowConflict(
                    "An investigation needs a finding before review"
                )

            if explanation_run_id is not None:
                cursor.execute(
                    """
                    SELECT 1
                    FROM ai.explanation_runs
                    WHERE run_id = %s
                      AND investigation_id = %s
                      AND status = 'SUCCEEDED'
                    """,
                    (explanation_run_id, investigation_id),
                )
                if cursor.fetchone() is None:
                    raise ApprovalWorkflowConflict(
                        "The explanation run is not a successful run for this case"
                    )

            cursor.execute(
                """
                UPDATE investigation.cases
                SET status = 'PENDING_APPROVAL',
                    updated_at = CURRENT_TIMESTAMP
                WHERE investigation_id = %s
                """,
                (investigation_id,),
            )
            cursor.execute(
                """
                INSERT INTO investigation.approval_events (
                    investigation_id,
                    actor_user_id,
                    explanation_run_id,
                    event_type,
                    previous_status,
                    new_status,
                    comment
                )
                VALUES (
                    %s, %s, %s, 'SUBMITTED_FOR_APPROVAL',
                    %s, 'PENDING_APPROVAL', %s
                )
                RETURNING
                    approval_event_id,
                    investigation_id,
                    actor_user_id,
                    explanation_run_id,
                    event_type,
                    previous_status,
                    new_status,
                    comment,
                    created_at
                """,
                (
                    investigation_id,
                    actor_user_id,
                    explanation_run_id,
                    previous_status,
                    comment,
                ),
            )
            return self._event(cursor.fetchone())

    def decide(
        self,
        investigation_id: int,
        actor_user_id: int,
        decision: InvestigationApprovalDecision,
        comment: str,
    ) -> InvestigationApprovalEvent:
        transitions = {
            InvestigationApprovalDecision.APPROVE: ("APPROVED", "APPROVED"),
            InvestigationApprovalDecision.REJECT: ("REJECTED", "REJECTED"),
            InvestigationApprovalDecision.REQUEST_CHANGES: (
                "CHANGES_REQUESTED",
                "INVESTIGATING",
            ),
        }
        event_type, new_status = transitions[decision]

        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT status
                FROM investigation.cases
                WHERE investigation_id = %s
                FOR UPDATE
                """,
                (investigation_id,),
            )
            case_row = cursor.fetchone()
            if case_row is None:
                raise InvestigationNotFoundError
            if case_row[0] != "PENDING_APPROVAL":
                raise ApprovalWorkflowConflict(
                    "The case is not waiting for an approval decision"
                )

            cursor.execute(
                """
                SELECT actor_user_id, explanation_run_id
                FROM investigation.approval_events
                WHERE investigation_id = %s
                  AND event_type = 'SUBMITTED_FOR_APPROVAL'
                ORDER BY approval_event_id DESC
                LIMIT 1
                """,
                (investigation_id,),
            )
            submission = cursor.fetchone()
            if submission is None:
                raise ApprovalWorkflowConflict(
                    "The case has no approval submission event"
                )
            if submission[0] == actor_user_id:
                raise ApprovalWorkflowConflict(
                    "The submitter cannot approve their own investigation"
                )

            cursor.execute(
                """
                UPDATE investigation.cases
                SET status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE investigation_id = %s
                """,
                (new_status, investigation_id),
            )
            cursor.execute(
                """
                INSERT INTO investigation.approval_events (
                    investigation_id,
                    actor_user_id,
                    explanation_run_id,
                    event_type,
                    previous_status,
                    new_status,
                    comment
                )
                VALUES (
                    %s, %s, %s, %s, 'PENDING_APPROVAL', %s, %s
                )
                RETURNING
                    approval_event_id,
                    investigation_id,
                    actor_user_id,
                    explanation_run_id,
                    event_type,
                    previous_status,
                    new_status,
                    comment,
                    created_at
                """,
                (
                    investigation_id,
                    actor_user_id,
                    submission[1],
                    event_type,
                    new_status,
                    comment,
                ),
            )
            return self._event(cursor.fetchone())

    def list_events(
        self,
        investigation_id: int,
    ) -> list[InvestigationApprovalEvent] | None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM investigation.cases
                WHERE investigation_id = %s
                """,
                (investigation_id,),
            )
            if cursor.fetchone() is None:
                return None

            cursor.execute(
                """
                SELECT
                    approval_event_id,
                    investigation_id,
                    actor_user_id,
                    explanation_run_id,
                    event_type,
                    previous_status,
                    new_status,
                    comment,
                    created_at
                FROM investigation.approval_events
                WHERE investigation_id = %s
                ORDER BY approval_event_id
                """,
                (investigation_id,),
            )
            rows = cursor.fetchall()

        return [self._event(row) for row in rows]

    @staticmethod
    def _event(row) -> InvestigationApprovalEvent:
        return InvestigationApprovalEvent(
            approval_event_id=row[0],
            investigation_id=row[1],
            actor_user_id=row[2],
            explanation_run_id=row[3],
            event_type=row[4],
            previous_status=row[5],
            new_status=row[6],
            comment=row[7],
            created_at=row[8],
        )