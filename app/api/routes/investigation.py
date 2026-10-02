from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Query

from app.application import create_investigation_application_service
from app.api.schemas import (
    InvestigationFindingResponse,
    InvestigationRecordResponse,
    InvestigationRunRequest,
    InvestigationSummaryResponse,
)
from app.database.connection import get_connection
from app.financial.models import InvestigationStatus
from app.auth.security import get_current_user, require_roles
from app.auth.models import Roles


router = APIRouter(
    prefix="/investigations",
    tags=["investigations"],
)


def get_db_connection() -> Generator:
    connection = get_connection()

    try:
        yield connection
    finally:
        connection.close()


@router.post("/settlements/{settlement_id}",response_model=InvestigationFindingResponse,)
def investigate_settlement(
    settlement_id: int,
    request: InvestigationRunRequest,
    connection=Depends(get_db_connection),
    current_user=Depends(
        require_roles(
            Roles.ANALYST,
            Roles.REVIEWER,
            Roles.ADMINISTRATOR,
        )
    ),
):
    service = create_investigation_application_service(connection)

    try:
        finding = service.investigate_settlement(
            settlement_id,
            investigation_type=request.investigation_type,
            idempotency_key=request.idempotency_key,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    if finding is None:
        raise HTTPException(
            status_code=404,
            detail="No discrepancy found for this settlement",
        )

    return InvestigationFindingResponse(
        root_causes=finding.root_causes,
        impact=str(finding.impact),
        severity=finding.severity,
        evidence=finding.evidence,
        recommended_action=finding.recommended_action,
    )


@router.get(
    "/",
    response_model=list[InvestigationSummaryResponse],
)
def list_investigations(
    settlement_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    investigation_type: str | None = Query(default=None),
    connection=Depends(get_db_connection),
    current_user=Depends(
        require_roles(
            Roles.ANALYST,
            Roles.REVIEWER,
            Roles.ADMINISTRATOR,
        )
    ),
):
    service = create_investigation_application_service(connection)

    return service.list_investigations(
        settlement_id=settlement_id,
        status=status,
        severity=severity,
        investigation_type=investigation_type,
    )


@router.get("/{investigation_id}",response_model=InvestigationRecordResponse,)
def get_investigation(
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
    service = create_investigation_application_service(connection)
    record = service.get_investigation(investigation_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation {investigation_id} not found",
        )

    finding_response = None
    if record.finding is not None:
        finding_response = InvestigationFindingResponse(
            root_causes=record.finding.root_causes,
            impact=str(record.finding.impact),
            severity=record.finding.severity,
            evidence=record.finding.evidence,
            recommended_action=record.finding.recommended_action,
        )

    return InvestigationRecordResponse(
        investigation_id=record.case.investigation_id,
        settlement_id=record.case.settlement_id,
        expected_cash=str(record.case.expected_cash),
        actual_cash=str(record.case.actual_cash),
        discrepancy=str(record.case.discrepancy),
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
        finding=finding_response,
    )

@router.put("/{investigation_id}/", deprecated=True)
def update_invetigation_status(
    investigation_id : int,
    status: InvestigationStatus,
    current_user=Depends(
        require_roles(
            Roles.REVIEWER,
            Roles.ADMINISTRATOR,
        )
    ),
):
    raise HTTPException(
        status_code=409,
        detail=(
            "Direct status updates are disabled. Use the approval workflow "
            "endpoints so each transition is recorded."
        ),
    )
    