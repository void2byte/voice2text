from rest_framework import serializers
from .models import PaymentTransaction
from minute_package_management.models import MinutePackage

class PaymentTransactionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    package_purchased = serializers.StringRelatedField()

    class Meta:
        model = PaymentTransaction
        fields = '__all__'
        read_only_fields = (
            'id', 'user', 'package_purchased', 'user_package_created',
            'transaction_id_gateway', 'payment_system', 'amount', 'currency',
            'status', 'created_at', 'updated_at', 'raw_response_gateway'
        )

class InitiatePaymentSerializer(serializers.Serializer):
    package_id = serializers.IntegerField(required=True)

    def validate_package_id(self, value):
        try:
            package = MinutePackage.objects.get(id=value, is_active=True)
        except MinutePackage.DoesNotExist:
            raise serializers.ValidationError("Выбранный пакет не найден или неактивен.")
        # Можно добавить дополнительные проверки, например, не покупает ли пользователь уже активный пакет такого же типа, если это не разрешено
        return value