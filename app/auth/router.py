from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.schemas import UserCreate, UserResponse, Token, RefreshTokenRequest
from app.auth.models import User
from app.auth.service import AuthService
from app.core.dependencies import get_auth_service, get_current_user, oauth2_scheme, rate_limit

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/register", response_model=UserResponse, status_code=201, dependencies=[Depends(rate_limit)])
async def register(
    request: Request, 
    user: UserCreate, 
    service: AuthService = Depends(get_auth_service)
):
    return await service.register(user)

@router.post("/login", response_model=Token, dependencies=[Depends(rate_limit)])
async def login(
    request: Request, 
    form_data: OAuth2PasswordRequestForm = Depends(), 
    service: AuthService = Depends(get_auth_service)
):
    return await service.login(form_data)

@router.post("/refresh", response_model=Token, dependencies=[Depends(rate_limit)])
async def refresh_token(
    request: Request, 
    refresh_request: RefreshTokenRequest, 
    service: AuthService = Depends(get_auth_service)
):
    return await service.refresh_token(refresh_request)

@router.post("/logout", status_code=204)
async def logout(
    request: Request, 
    token: str = Depends(oauth2_scheme),
    refresh_request: RefreshTokenRequest = None,
    service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user)
):
    refresh_token = refresh_request.refresh_token if refresh_request else None
    await service.logout(access_token=token, refresh_token=refresh_token)
    return None
