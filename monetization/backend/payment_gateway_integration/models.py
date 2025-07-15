from django.db import models
from django.conf import settings
from minute_package_management.models import MinutePackage, UserPackage

class PaymentTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидание'),
        ('completed', 'Завершено'),
        ('failed', 'Ошибка'),
        ('refunded', 'Возвращено'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    package_purchased = models.ForeignKey(MinutePackage, on_delete=models.SET_NULL, null=True, blank=True)
    user_package_created = models.OneToOneField(UserPackage, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_transaction')
    
    transaction_id_gateway = models.CharField(max_length=255, unique=True, help_text="ID транзакции от платежного шлюза")
    payment_system = models.CharField(max_length=50, help_text="Название платежной системы (например, Stripe, YooKassa)")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='RUB') # или другая валюта
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    raw_response_gateway = models.TextField(blank=True, help_text="Полный ответ от платежного шлюза")

    def __str__(self):
        return f"Транзакция {self.transaction_id_gateway} ({self.status}) - {self.amount} {self.currency}"

    class Meta:
        ordering = ['-created_at']