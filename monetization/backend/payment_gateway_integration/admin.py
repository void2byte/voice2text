from django.contrib import admin
from .models import PaymentTransaction

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'package_purchased', 'transaction_id_gateway', 'payment_system', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('status', 'payment_system', 'currency', 'created_at')
    search_fields = ('user__username', 'transaction_id_gateway', 'package_purchased__name')
    readonly_fields = ('created_at', 'updated_at', 'raw_response_gateway', 'user_package_created')
    # Можно добавить действия, например, для попытки возврата платежа (если поддерживается шлюзом)