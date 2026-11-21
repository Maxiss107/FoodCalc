from django.http import HttpRequest
from ninja import Router, Status
from ninja_jwt.authentication import JWTAuth

from apps.accounts.schemas import (
    ErrorSchema,
    LoginSchema,
    RegisterSchema,
    TokenPairSchema,
    TokenRefreshSchema,
    UserOutSchema,
)
from apps.accounts.services import login_user, refresh_tokens, register_user

router = Router(tags=["Auth"])
jwt_auth = JWTAuth()


@router.post(
    "/register",
    response={201: TokenPairSchema, 409: ErrorSchema},
)
def register(request: HttpRequest, payload: RegisterSchema) -> Status[dict[str, str]]:
    """Регистрация нового пользователя по email и паролю."""
    tokens = register_user(email=payload.email, password=payload.password)
    return Status(201, tokens)


@router.post(
    "/login",
    response={200: TokenPairSchema, 401: ErrorSchema},
)
def login(request: HttpRequest, payload: LoginSchema) -> dict[str, str]:
    """Вход по email и паролю с выдачей пары JWT-токенов."""
    return login_user(request=request, email=payload.email, password=payload.password)


@router.post(
    "/refresh",
    response={200: TokenPairSchema, 401: ErrorSchema},
)
def refresh(request: HttpRequest, payload: TokenRefreshSchema) -> dict[str, str]:
    """Обновление access-токена по refresh-токену."""
    return refresh_tokens(refresh_token=payload.refresh)


@router.get(
    "/me",
    auth=jwt_auth,
    response={200: UserOutSchema},
)
def me(request: HttpRequest) -> object:
    """Возвращает профиль текущего аутентифицированного пользователя."""
    return request.auth
