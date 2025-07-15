from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Дополнительные поля для пользователя, если необходимо
    # Например, Telegram ID, если он будет использоваться для идентификации
    telegram_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    # Другие поля, специфичные для вашего приложения

    def __str__(self):
        return self.username