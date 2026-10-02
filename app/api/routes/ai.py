import logging
import os

from fastapi import APIRouter, Depends, HTTPException

from app.ai.agent import InvestigationExplanationAgent
from app.ai.explanation_service import (
    DeterministicExplanationProvider,
)
from app.ai.llm_provider import LLMExplanationProvider
from app.ai.llm_provider import LLMProviderUnavailableError
from app.ai.tools import InvestigationReadOnlyTools
from app.api.routes.investigation import get_db_connection
from app.api.schemas import InvestigationExplanationResponse
from app.auth.models import Roles
from app.auth.security import require_roles
from app.database.connection import get_connection
from app.database.repositories.ai_explanation_audit_repository import (
    AIExplanationAuditRepository,
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/ai",
    tags=["ai"],
)


def get_ai_audit_repository():
    connection = get_connection()

    try:
        yield AIExplanationAuditRepository(connection)
    finally:
        connection.close()


def create_explanation_service(connection, audit_repository):
    provider_name = os.environ.get("AI_PROVIDER", "mock").strip().lower()

    if provider_name == "llm":
        provider = LLMExplanationProvider(
            api_key=os.environ.get("LLM_API_KEY"),
            model=os.environ.get("LLM_MODEL"),
            endpoint=os.environ.get(
                "LLM_ENDPOINT"
            ),
            max_retries=int(os.environ.get("LLM_MAX_RETRIES", "2")),
            retry_delay_seconds=float(
                os.environ.get("LLM_RETRY_DELAY_SECONDS", "1")
            ),
            request_timeout_seconds=float(
                os.environ.get("LLM_REQUEST_TIMEOUT_SECONDS", "30")
            ),
        )
    elif provider_name == "mock":
        provider = DeterministicExplanationProvider()
    else:
        raise ValueError(f"Unsupported AI_PROVIDER: {provider_name}")

    return InvestigationExplanationAgent(
        tools=InvestigationReadOnlyTools(connection),
        provider=provider,
        audit_repository=audit_repository,
    )


@router.post(
    "/investigations/{investigation_id}/explanation",
    response_model=InvestigationExplanationResponse,
)
def explain_investigation(
    investigation_id: int,
    connection=Depends(get_db_connection),
    audit_repository=Depends(get_ai_audit_repository),
    current_user=Depends(
        require_roles(
            Roles.ANALYST,
            Roles.REVIEWER,
            Roles.ADMINISTRATOR,
        )
    ),
):
    try:
        agent = create_explanation_service(connection, audit_repository)
        explanation = agent.explain_investigation(
            investigation_id,
            current_user.user_id,
        )
    except (LLMProviderUnavailableError, ValueError):
        logger.exception(
            "AI explanation failed for investigation_id=%s",
            investigation_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
        ) from None
    except Exception:
        logger.exception(
            "Unexpected AI explanation failure for investigation_id=%s",
            investigation_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
        ) from None

    if explanation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation {investigation_id} not found",
        )

    return explanation
