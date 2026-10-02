from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from psycopg.errors import UniqueViolation

from app.api.schemas import UserCreateRequest, UserResponse
from app.auth.user_repository import UserRepository
from app.auth.user_service import UserService
from app.database.connection import get_connection
from app.auth.models import Roles, TokenResponse
from app.auth.security import create_access_token, require_roles


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


def get_db_connection() -> Generator:
    connection = get_connection()

    try:
        yield connection
    finally:
        connection.close()


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    request: UserCreateRequest,
    connection=Depends(get_db_connection),
    current_user=Depends(require_roles(Roles.ADMINISTRATOR)),

):
    service = UserService(UserRepository(connection), connection)

    try:
        user = service.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            role=request.role,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except UniqueViolation as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with that email already exists",
        ) from error

    return UserResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
    )

@router.post(
    "/token",
    response_model=TokenResponse,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    connection=Depends(get_db_connection),
):
    repository = UserRepository(connection)

    user = repository.verify_password(
        email=form_data.username,
        password=form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    token = create_access_token(
        user_id=user.user_id,
        email=user.email,
        role=user.role,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )