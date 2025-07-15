from django.db import models
from django.conf import settings

class MinutePackage(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    minutes_amount = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True) # Можно деактивировать пакеты, не удаляя их
    # Поле для срока действия пакета, если необходимо
    # duration_days = models.PositiveIntegerField(null=True, blank=True, help_text="Срок действия пакета в днях после покупки")

    def __str__(self):
        return f"{self.name} - {self.minutes_amount} минут за {self.price} руб."

class UserPackage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='minute_packages')
    package = models.ForeignKey(MinutePackage, on_delete=models.PROTECT) # Защита от удаления пакета, если он куплен
    purchase_date = models.DateTimeField(auto_now_add=True)
    # expiration_date = models.DateTimeField(null=True, blank=True) # Рассчитывается при покупке, если есть duration_days
    minutes_remaining = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True) # Может быть деактивирован, например, по истечении срока

    def __str__(self):
        return f"{self.user.username} - {self.package.name} ({self.minutes_remaining} мин. осталось)"

    def save(self, *args, **kwargs):
        if self._state.adding: # Если это новая запись (покупка пакета)
            self.minutes_remaining = self.package.minutes_amount
            # if self.package.duration_days:
            #     from datetime import timedelta
            #     self.expiration_date = self.purchase_date + timedelta(days=self.package.duration_days)
        super().save(*args, **kwargs)