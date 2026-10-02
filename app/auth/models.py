from enum import Enum

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserLoginRequest(BaseModel):
    username: str
    password: str

class Roles(Enum):
    ANALYST = 'ANALYST'
    REVIEWER = 'REVIEWER'
    ADMINISTRATOR = 'ADMINISTRATOR'