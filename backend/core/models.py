import uuid

from django.conf import settings
from django.db import models


class CoreModel(models.Model):
    """
    Абстрактная базовая модель для всех сущностей проекта.
    Задает единый первичный ключ UUID v4 и автоматические метки времени.
    Используется напрямую для связующих и дочерних таблиц.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date of creation",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date of update",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class OwnedModel(CoreModel):
    """
    Абстрактная базовая модель для корневых сущностей, принадлежащих пользователю.
    Поле owner:
    - у личных записей указывает на аккаунт мастера;
    - у базовых шаблонов указывает на системного пользователя (User.objects.get_system_user()).
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)ss",
        verbose_name="Owner",
    )

    class Meta(CoreModel.Meta):
        abstract = True
