from django.contrib.auth import authenticate
from django.http import HttpRequest
from ninja.errors import HttpError
from ninja_jwt.exceptions import TokenError
from ninja_jwt.tokens import RefreshToken

from apps.accounts.models import User


def get_tokens_for_user(user: User) -> dict[str, str]:
    """Генерирует пару access и refresh JWT-токенов для пользователя."""
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "token_type": "bearer",
    }


def register_user(email: str, password: str) -> dict[str, str]:
    """Регистрирует нового пользователя и возвращает пару access и refresh JWT-токенов."""
    normalized_email = email.strip().lower()
    if User.objects.filter(email__iexact=normalized_email).exists():
        raise HttpError(409, "User with this email already exists.")

    user = User.objects.create_user(email=normalized_email, password=password)
    return get_tokens_for_user(user)


def login_user(request: HttpRequest, email: str, password: str) -> dict[str, str]:
    """Проверяет email и пароль через Django auth и возвращает пару токенов."""
    normalized_email = email.strip().lower()
    user = authenticate(request, email=normalized_email, password=password)

    if user is None or not user.is_active or getattr(user, "is_system", False):
        raise HttpError(401, "Invalid email or password.")

    return get_tokens_for_user(user)


def refresh_tokens(refresh_token: str) -> dict[str, str]:
    """Выдаёт новый access-токен по валидному refresh-токену."""
    try:
        refresh = RefreshToken(refresh_token)
    except TokenError as exc:
        raise HttpError(401, "Invalid or expired refresh token.") from exc

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "token_type": "bearer",
    }
