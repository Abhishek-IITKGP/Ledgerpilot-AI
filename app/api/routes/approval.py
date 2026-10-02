from fastapi import APIRouter, Depends, HTTPException

from app.api.routes.investigation import get_db_connection
from app.api.schemas import (
    InvestigationApprovalDecisionRequest,
    InvestigationApprovalEventResponse,
    SubmitForApprovalRequest,
)
from app.auth.models import Roles
from app.auth.security import require_roles
from app.database.repositories.investigation_approval_repository import (
    InvestigationApprovalRepository,
)
from app.investigation.approval_errors import (
    ApprovalWorkflowConflict,
    InvestigationNotFoundError,
)
from app.investigation.approval_service import InvestigationApprovalService


router = APIRouter(
    prefix="/investigations",
    tags=["investigation approvals"],
)


@router.get(
    "/{investigation_id}/approval-events",
    response_model=list[InvestigationApprovalEventResponse],
)
def list_approval_events(
    investigation_id: int,
    connection=Depends(get_db_connection),
    current_user=Depends(
        require_roles(
            Roles.ANALYST,
            Roles.REVIEWER,
            Roles.ADMINISTRATOR,
        )
    ),
):
    service = InvestigationApprovalService(
        connection,
        InvestigationApprovalRepository(connection),
    )
    events = service.list_events(investigation_id)

    if events is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found",
        )

    return events


@router.post(
    "/{investigation_id}/submit-for-approval",
    response_model=InvestigationApprovalEventResponse,
)
def submit_for_approval(
    investigation_id: int,
    request: SubmitForApprovalRequest,
    connection=Depends(get_db_connection),
    current_user=Depends(
        require_roles(
            Roles.ANALYST,
            Roles.REVIEWER,
            Roles.ADMINISTRATOR,
        )
    ),
):
    service = InvestigationApprovalService(
        connection,
        InvestigationApprovalRepository(connection),
    )

    try:
        return service.submit_for_approval(
            investigation_id=investigation_id,
            actor_user_id=current_user.user_id,
            comment=request.comment,
            explanation_run_id=request.explanation_run_id,
        )
    except InvestigationNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found",
        ) from error
    except ApprovalWorkflowConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post(
    "/{investigation_id}/decision",
    response_model=InvestigationApprovalEventResponse,
)
def decide_on_investigation(
    investigation_id: int,
    request: InvestigationApprovalDecisionRequest,
    connection=Depends(get_db_connection),
    current_user=Depends(
        require_roles(
            Roles.REVIEWER,
            Roles.ADMINISTRATOR,
        )
    ),
):
    service = InvestigationApprovalService(
        connection,
        InvestigationApprovalRepository(connection),
    )

    try:
        return service.decide(
            investigation_id=investigation_id,
            actor_user_id=current_user.user_id,
            decision=request.decision,
            comment=request.comment,
        )
    except InvestigationNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found",
        ) from error
    except ApprovalWorkflowConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from error