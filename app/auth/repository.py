import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.auth.models import User, RefreshSession

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

class RefreshSessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_token(self, token: str) -> Optional[RefreshSession]:
        result = await self.session.execute(select(RefreshSession).where(RefreshSession.refresh_token == token))
        return result.scalars().first()

    async def create(self, session_data: RefreshSession) -> RefreshSession:
        self.session.add(session_data)
        await self.session.commit()
        await self.session.refresh(session_data)
        return session_data

    async def delete_by_token(self, token: str) -> bool:
        result = await self.session.execute(select(RefreshSession).where(RefreshSession.refresh_token == token))
        session_obj = result.scalars().first()
        if session_obj:
            await self.session.delete(session_obj)
            await self.session.commit()
            return True
        return False
