from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import MinutePackage, UserPackage
from .serializers import MinutePackageSerializer, UserPackageSerializer #, PurchasePackageSerializer

class MinutePackageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API эндпоинт для просмотра доступных пакетов минут.
    """
    queryset = MinutePackage.objects.filter(is_active=True)
    serializer_class = MinutePackageSerializer
    permission_classes = [permissions.IsAuthenticated] # Доступно всем аутентифицированным пользователям

class UserPackageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API эндпоинт для просмотра купленных пользователем пакетов минут.
    """
    serializer_class = UserPackageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserPackage.objects.filter(user=self.request.user, is_active=True).order_by('purchase_date')

    # Действие для покупки пакета будет реализовано в модуле интеграции с платежной системой
    # или в отдельном эндпоинте, который обрабатывает весь процесс покупки.

    # Пример действия для списания минут (может быть частью другого модуля, например, API Screph)
    # @action(detail=True, methods=['post'])
    # def spend_minutes(self, request, pk=None):
    #     user_package = self.get_object()
    #     minutes_to_spend = request.data.get('minutes')

    #     if minutes_to_spend is None or not isinstance(minutes_to_spend, int) or minutes_to_spend <= 0:
    #         return Response({'error': 'Необходимо указать корректное количество минут для списания.'}, status=status.HTTP_400_BAD_REQUEST)

    #     if user_package.minutes_remaining < minutes_to_spend:
    #         return Response({'error': 'Недостаточно минут на балансе.'}, status=status.HTTP_400_BAD_REQUEST)
        
    #     user_package.minutes_remaining -= minutes_to_spend
    #     if user_package.minutes_remaining == 0:
    #         user_package.is_active = False # Деактивировать пакет, если минуты закончились
    #     user_package.save()
    #     return Response(UserPackageSerializer(user_package).data)

# Можно добавить представления для администратора для CRUD операций с MinutePackage,
# если не используется стандартная админка Django или admin_panel.