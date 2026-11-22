from datetime import datetime
from uuid import UUID

from ninja import Schema
from pydantic import EmailStr, Field


class RegisterSchema(Schema):
    """Входные данные для регистрации нового пользователя (POST /api/auth/register)."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginSchema(Schema):
    """Входные данные для входа пользователя по email и паролю (POST /api/auth/login)."""

    email: EmailStr
    password: str
    remember_me: bool = False


class TokenRefreshSchema(Schema):
    """Входные данные для обновления access-токена по refresh-токену (POST /api/auth/refresh)."""

    refresh: str


class TokenPairSchema(Schema):
    """Ответ сервера с парой access и refresh JWT-токенов после входа, регистрации или обновления."""

    access: str
    refresh: str
    token_type: str = "bearer"


class UserOutSchema(Schema):
    """Публичные данные профиля текущего пользователя без пароля (GET /api/auth/me)."""

    id: UUID
    email: str
    is_active: bool
    created_at: datetime


class ErrorSchema(Schema):
    """Формат ответа при ошибке аутентификации или конфликте данных (401, 409)."""

    detail: str
