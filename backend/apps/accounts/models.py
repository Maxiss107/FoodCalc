from typing import Any

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import IntegrityError, models, transaction

from core.config import config
from core.models import CoreModel


class UserManager(BaseUserManager["User"]):
    """
    Менеджер кастомной модели пользователя.

    Обеспечивает:
    - аутентификацию пользователя по адресу электронной почты;
    - хеширование паролей средствами Django (set_password / check_password);
    - доступ к системной учетной записи (get_system_user), являющейся
        владельцем общих шаблонов рецептов и базовых ингредиентов.
    """

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        """
        Создание пользователя с указанным адресом электронной почты.

        Перед сохранением выполняет нормализацию email-адреса (приведение
        доменной части к нижнему регистру). При передаче непустого пароля
        хеширует его средствами Django; при отсутствии пароля отключает
        возможность аутентификации по паролю посредством вызова
        set_unusable_password.

        В случае отсутствия email выбрасывает исключение ValueError.
        """
        if not email:
            raise ValueError("Email field is required.")

        normalized_email = self.normalize_email(email).lower()
        user = self.model(email=normalized_email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        """
        Создание суперпользователя с расшифненными правами доступа.

        По умолчанию устанавливает флаги is_staff, is_superuser и is_active
        в значение True. При передаче невалидных значений выбрасывает
        исключение ValueError.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email=email, password=password, **extra_fields)

    def get_system_user(self) -> "User":
        """
        Возвращает системную учетную запись. При ее отсутствии создает новую
        посредством вызова create_user с пустым паролем.

        Системная учетная запись выступает владельцем общих шаблонов рецептов
        и базовых ингредиентов. Аутентификация по паролю для создаваемой
        записи отключена (реализация — в методе create_user).

        Обработка гонки при параллельном создании выполняется через
        перехват исключения IntegrityError и повторное получение записи.
        """
        try:
            return self.get(email=config.SYSTEM_USER_EMAIL)
        except self.model.DoesNotExist:
            try:
                with transaction.atomic():
                    return self.create_user(
                        email=config.SYSTEM_USER_EMAIL,
                        password=None,
                        is_system=True,
                        is_active=True,
                        is_staff=False,
                    )
            except IntegrityError:
                return self.get(email=config.SYSTEM_USER_EMAIL)


class User(AbstractBaseUser, PermissionsMixin, CoreModel):
    """
    Кастомная модель пользователя.

    Наследование:
    - от CoreModel - первичный ключ id (UUID v4), временные метки
        created_at и updated_at;
    - от AbstractBaseUser - поле password (хранилище хеша пароля) и
        методы set_password / check_password.

    Регистрация в проекте выполняется посредством параметра
    AUTH_USER_MODEL = "accounts.User" в модуле core/settings.py.
    """

    email = models.EmailField(
        max_length=255,
        unique=True,
        verbose_name="Email",
    )
    is_system = models.BooleanField(
        default=False,
        editable=False,
        verbose_name="Template System Account",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active",
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Access to the admin panel",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return self.email
