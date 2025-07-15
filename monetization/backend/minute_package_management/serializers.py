from rest_framework import serializers
from .models import MinutePackage, UserPackage

class MinutePackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MinutePackage
        fields = ['id', 'name', 'description', 'minutes_amount', 'price', 'is_active']

class UserPackageSerializer(serializers.ModelSerializer):
    package = MinutePackageSerializer(read_only=True) # Отображаем детали пакета, а не только ID
    # user = serializers.StringRelatedField() # Можно использовать для отображения username

    class Meta:
        model = UserPackage
        fields = ['id', 'user', 'package', 'purchase_date', 'minutes_remaining', 'is_active']
        read_only_fields = ['id', 'user', 'purchase_date']

# Сериализатор для процесса покупки (может понадобиться позже)
# class PurchasePackageSerializer(serializers.Serializer):
#     package_id = serializers.IntegerField()
    
#     def validate_package_id(self, value):
#         try:
#             package = MinutePackage.objects.get(id=value, is_active=True)
#         except MinutePackage.DoesNotExist:
#             raise serializers.ValidationError("Выбранный пакет не найден или неактивен.")
#         return value