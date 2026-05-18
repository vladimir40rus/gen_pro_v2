from datetime import datetime
from typing import Optional
from passlib.context import CryptContext

from app.domain.entity.user import User
from app.application_logic.dto.user_dto import UserCreateDTO, UserResponseDTO, UserUpdateDTO, UserStatsDTO
from app.infra_external.repositories.user_repo import UserRepo

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """Сервис для работы с пользователями"""

    def __init__(self, user_repo: UserRepo):
        self.user_repo = user_repo

    def _hash_password(self, password: str) -> str:
        """Хэширование пароля"""
        return pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return pwd_context.verify(plain_password, hashed_password)

    async def create_user(self, user_dto: UserCreateDTO) -> UserResponseDTO:
        """Создание пользователя"""
        # Проверка уникальности
        existing = await self.user_repo.get_by_username(user_dto.username)
        if existing:
            raise ValueError("Username already exists")

        existing = await self.user_repo.get_by_email(user_dto.email)
        if existing:
            raise ValueError("Email already exists")

        # Хэширование пароля
        hashed_password = self._hash_password(user_dto.password)

        # Создание пользователя
        db_user = await self.user_repo.create(
            username=user_dto.username,
            email=user_dto.email,
            password_hash=hashed_password
        )

        return UserResponseDTO(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            bio=db_user.bio,
            image_url=db_user.image_url,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        )

    async def get_current_user(self) -> Optional[UserResponseDTO]:
        """Получить текущего пользователя (временно, пока нет JWT)"""
        db_user = await self.user_repo.get_current_user()
        if not db_user:
            return None

        return UserResponseDTO(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            bio=db_user.bio,
            image_url=db_user.image_url,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        )

    async def update_user(self, user_dto: UserUpdateDTO, current_user_id: int) -> UserResponseDTO:
        """Обновление пользователя"""
        db_user = await self.user_repo.get_by_id(current_user_id)
        if not db_user:
            raise ValueError("User not found")

        # Обновление полей
        if user_dto.username:
            existing = await self.user_repo.get_by_username(user_dto.username)
            if existing and existing.id != current_user_id:
                raise ValueError("Username already exists")
            db_user.username = user_dto.username

        if user_dto.email:
            existing = await self.user_repo.get_by_email(user_dto.email)
            if existing and existing.id != current_user_id:
                raise ValueError("Email already exists")
            db_user.email = user_dto.email

        if user_dto.bio is not None:
            db_user.bio = user_dto.bio

        if user_dto.image_url is not None:
            db_user.image_url = user_dto.image_url

        db_user.updated_at = datetime.now()
        await self.user_repo.update(db_user)

        return UserResponseDTO(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            bio=db_user.bio,
            image_url=db_user.image_url,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        )

    async def get_user_stats(self, username: str) -> UserStatsDTO:
        """Получение статистики пользователя"""
        db_user = await self.user_repo.get_by_username(username)
        if not db_user:
            raise ValueError(f"User '{username}' not found")

        stats = await self.user_repo.get_stats(db_user.id)

        return UserStatsDTO(
            username=db_user.username,
            articles_published=stats["articles_count"],
            total_likes_received=0,  # TODO: реализовать
            total_comments_received=stats["comments_count"],
            followers_count=stats["followers_count"],
            following_count=stats["following_count"],
            joined_date=db_user.created_at.strftime("%Y-%m-%d")
        )


async def get_user_service(user_repo: UserRepo) -> UserService:
    """Dependency для получения UserService"""
    return UserService(user_repo)