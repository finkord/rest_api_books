from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.schemas import UserCreate, UserResponse, Token, RefreshTokenRequest, MessageResponse
from app.auth.service import AuthService
from app.core.dependencies import get_auth_service

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user: UserCreate, service: AuthService = Depends(get_auth_service)):
    return await service.register(user)

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), service: AuthService = Depends(get_auth_service)):
    return await service.login(form_data)

@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest, service: AuthService = Depends(get_auth_service)):
    return await service.refresh_token(request)
