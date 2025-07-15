from rest_framework import views, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from minute_package_management.models import UserPackage
from minute_package_management.serializers import UserPackageSerializer
from user_management.serializers import UserSerializer # Для информации о пользователе

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile_with_balance(request):
    """
    Возвращает профиль пользователя и его активные пакеты минут.
    """
    user = request.user
    user_serializer = UserSerializer(user)
    active_packages = UserPackage.objects.filter(user=user, is_active=True, minutes_remaining__gt=0).order_by('purchase_date')
    packages_serializer = UserPackageSerializer(active_packages, many=True)
    
    total_minutes_remaining = sum(pkg.minutes_remaining for pkg in active_packages)
    
    return Response({
        'user': user_serializer.data,
        'active_packages': packages_serializer.data,
        'total_minutes_remaining': total_minutes_remaining
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def spend_minutes_api(request):
    """
    Эндпоинт для списания минут пользователя.
    Принимает 'minutes_to_spend' в теле запроса.
    Списывает минуты из самого старого активного пакета.
    """
    minutes_to_spend = request.data.get('minutes_to_spend')

    if minutes_to_spend is None or not isinstance(minutes_to_spend, int) or minutes_to_spend <= 0:
        return Response({'error': 'Необходимо указать корректное количество минут для списания (целое положительное число).'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    # Получаем самый старый активный пакет с достаточным количеством минут
    # Сначала пытаемся найти пакет, который может покрыть весь запрос
    user_package = UserPackage.objects.filter(
        user=user, 
        is_active=True, 
        minutes_remaining__gte=minutes_to_spend
    ).order_by('purchase_date').first()

    # Если такого пакета нет, но есть активные пакеты, будем списывать последовательно
    # (эта логика усложнена, для начала спишем с первого подходящего или вернем ошибку)
    # Для упрощения, если нет одного пакета, который может покрыть все, вернем ошибку или потребуем списать меньше.
    # Более сложная логика: списать с нескольких пакетов.

    if not user_package:
        # Проверим, есть ли вообще минуты
        total_available_minutes = sum(p.minutes_remaining for p in UserPackage.objects.filter(user=user, is_active=True))
        if total_available_minutes == 0:
             return Response({'error': 'У вас нет доступных минут.'}, status=status.HTTP_400_BAD_REQUEST)
        elif total_available_minutes < minutes_to_spend:
            return Response({'error': f'Недостаточно минут для списания. Доступно: {total_available_minutes} мин.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Эта ситуация означает, что минуты есть, но распределены по пакетам так, что ни один не покрывает запрос целиком.
            # Требуется более сложная логика списания с нескольких пакетов, пока оставим как ошибку.
            return Response({'error': 'Не удалось найти один пакет для списания указанного количества минут. Попробуйте списать меньшее количество или обратитесь в поддержку для реализации списания с нескольких пакетов.'}, status=status.HTTP_400_BAD_REQUEST)

    user_package.minutes_remaining -= minutes_to_spend
    if user_package.minutes_remaining == 0:
        user_package.is_active = False # Деактивировать пакет, если минуты закончились
    user_package.save()

    return Response({
        'message': f'{minutes_to_spend} минут успешно списано.',
        'package_updated': UserPackageSerializer(user_package).data,
        'total_minutes_remaining': sum(p.minutes_remaining for p in UserPackage.objects.filter(user=user, is_active=True))
    }, status=status.HTTP_200_OK)

# Другие общие API эндпоинты могут быть добавлены здесь