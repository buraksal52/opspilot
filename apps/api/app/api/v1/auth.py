from fastapi import APIRouter, Depends

from app.api.v1.deps import get_auth_service
from app.api.v1.schemas.auth import LoginRequest, TokenResponse
from app.application.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, auth_service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    access_token = await auth_service.login(request.email, request.password)
    return TokenResponse(access_token=access_token)
