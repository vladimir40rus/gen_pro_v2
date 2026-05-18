from passlib.context import CryptContext
from app.infra_external.repositories.user_repo import UserRepo

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Сервис для аутентификации"""

    def __init__(self, user_repo: UserRepo):
        self.user_repo = user_repo

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        """Хэширование пароля"""
        return pwd_context.hash(password)

    async def authenticate_user(self, email: str, password: str):
        """Аутентификация пользователя"""
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None

        if not self.verify_password(password, user.password_hash):
            return None

        return user


async def get_auth_service(user_repo: UserRepo) -> AuthService:
    """Dependency для получения AuthService"""
    return AuthService(user_repo)