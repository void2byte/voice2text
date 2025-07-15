from django.db import models
from django.contrib.auth.models import User

class MinutePackage(models.Model):
    name = models.CharField(max_length=100, unique=True)
    minutes = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True) # Полезно для временного отключения пакета
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.minutes} мин.) - ${self.price}"

    class Meta:
        ordering = ['price'] # Сортировка по умолчанию

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # Дополнительные поля для пользователя, если нужны, например:
    # remaining_minutes = models.PositiveIntegerField(default=0)
    # telegram_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

# Можно добавить модель для отслеживания покупок пакетов пользователями
class PurchaseHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    package = models.ForeignKey(MinutePackage, on_delete=models.SET_NULL, null=True) # SET_NULL, если пакет удален, история сохраняется
    purchase_date = models.DateTimeField(auto_now_add=True)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    minutes_at_purchase = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.user.username} - {self.package.name if self.package else 'N/A'} on {self.purchase_date.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-purchase_date']