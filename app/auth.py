from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import UserCreate, UserResponse, Token, RefreshTokenRequest
from app.dependencies import get_db
from app.services import AuthService
from app.repository import UserRepository

router = APIRouter(prefix="/api/auth", tags=["Auth"])

async def get_auth_service(db: AsyncSession = Depends(get_db)):
    return AuthService(repository=UserRepository(db))

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user: UserCreate, service: AuthService = Depends(get_auth_service)):
    return await service.register(user)

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), service: AuthService = Depends(get_auth_service)):
    return await service.login(form_data)

@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest, service: AuthService = Depends(get_auth_service)):
    return await service.refresh_token(request)
