from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.schemas import UserCreate, UserResponse, Token, RefreshTokenRequest
from app.auth.service import AuthService
from app.core.dependencies import get_auth_service, rate_limit

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(request: Request, user: UserCreate, service: AuthService = Depends(get_auth_service)):
    await rate_limit(request)
    return await service.register(user)

@router.post("/login", response_model=Token)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), service: AuthService = Depends(get_auth_service)):
    # await rate_limit(request)
    return await service.login(form_data)

@router.post("/refresh", response_model=Token)
async def refresh_token(request: Request, refresh_request: RefreshTokenRequest, service: AuthService = Depends(get_auth_service)):
    await rate_limit(request)
    return await service.refresh_token(refresh_request)
