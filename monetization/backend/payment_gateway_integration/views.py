from django.shortcuts import redirect, get_object_or_404
from django.conf import settings
from django.urls import reverse
from rest_framework import views, status, permissions
from rest_framework.response import Response
import uuid # Для генерации уникальных ID заказов, если шлюз этого требует

from .models import PaymentTransaction
from minute_package_management.models import MinutePackage, UserPackage
from .serializers import PaymentTransactionSerializer, InitiatePaymentSerializer

# Заглушки для переменных, которые должны быть в settings.py
# YOOKASSA_SHOP_ID = getattr(settings, 'YOOKASSA_SHOP_ID', None)
# YOOKASSA_SECRET_KEY = getattr(settings, 'YOOKASSA_SECRET_KEY', None)
# STRIPE_SECRET_KEY = getattr(settings, 'STRIPE_SECRET_KEY', None)
# STRIPE_PUBLISHABLE_KEY = getattr(settings, 'STRIPE_PUBLISHABLE_KEY', None)

class InitiatePaymentView(views.APIView):
    """
    Эндпоинт для инициации процесса оплаты.
    Принимает ID пакета, создает транзакцию в статусе 'pending'
    и перенаправляет пользователя на страницу оплаты шлюза (или возвращает URL).
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InitiatePaymentSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        package_id = serializer.validated_data['package_id']
        try:
            package = MinutePackage.objects.get(id=package_id, is_active=True)
        except MinutePackage.DoesNotExist:
            return Response({'error': 'Пакет не найден или неактивен.'}, status=status.HTTP_404_NOT_FOUND)

        # Создаем транзакцию в нашей системе
        transaction = PaymentTransaction.objects.create(
            user=request.user,
            package_purchased=package,
            amount=package.price,
            currency='RUB', # или из настроек пакета/проекта
            status='pending',
            payment_system='placeholder_gateway', # Заменить на реальный шлюз
            transaction_id_gateway=f"placeholder_{uuid.uuid4()}" # Заменить на реальный ID от шлюза
        )

        # Здесь должна быть логика взаимодействия с платежным шлюзом
        # Например, для YooKassa:
        # from yookassa import Configuration, Payment
        # Configuration.account_id = YOOKASSA_SHOP_ID
        # Configuration.secret_key = YOOKASSA_SECRET_KEY
        # payment = Payment.create({
        #     "amount": {
        #         "value": str(package.price),
        #         "currency": "RUB"
        #     },
        #     "confirmation": {
        #         "type": "redirect",
        #         "return_url": request.build_absolute_uri(reverse('payment_success_callback')) # URL для коллбэка
        #     },
        #     "capture": True,
        #     "description": f"Покупка пакета: {package.name}",
        #     "metadata": {
        #         'transaction_db_id': transaction.id
        #     }
        # })
        # transaction.transaction_id_gateway = payment.id
        # transaction.save()
        # return Response({'confirmation_url': payment.confirmation.confirmation_url}, status=status.HTTP_201_CREATED)

        # Заглушка: возвращаем информацию о созданной транзакции и фейковый URL
        return Response({
            'message': 'Платеж инициирован (заглушка).',
            'transaction_id': transaction.id,
            'package_name': package.name,
            'amount': package.price,
            'confirmation_url': f'https://placeholder-payment-gateway.com/pay?order_id={transaction.transaction_id_gateway}'
        }, status=status.HTTP_201_CREATED)

class PaymentWebhookView(views.APIView):
    """
    Эндпоинт для приема webhook-уведомлений от платежного шлюза.
    Обновляет статус транзакции и, в случае успеха, создает UserPackage.
    Этот эндпоинт должен быть доступен без аутентификации, но защищен (например, проверкой подписи шлюза).
    """
    permission_classes = [permissions.AllowAny] # Осторожно! Нужна валидация запроса от шлюза.

    def post(self, request, *args, **kwargs):
        # Здесь должна быть логика обработки уведомления от шлюза
        # 1. Валидация запроса (проверка IP, подписи и т.д.)
        # 2. Получение данных о платеже (event, object_id и т.д.)
        # 3. Поиск транзакции в нашей БД по ID из уведомления
        # 4. Обновление статуса транзакции
        # 5. Если платеж успешен (status='completed'):
        #    - Создать UserPackage для пользователя
        #    - Отправить пользователю уведомление об успешной покупке

        # Примерная логика (заглушка):
        payload = request.data
        gateway_transaction_id = payload.get('object', {}).get('id') # Зависит от структуры ответа шлюза
        payment_status_gateway = payload.get('event') # Например, 'payment.succeeded' или 'payment.failed'

        if not gateway_transaction_id or not payment_status_gateway:
            return Response({'error': 'Некорректные данные от шлюза.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transaction = PaymentTransaction.objects.get(transaction_id_gateway=gateway_transaction_id)
        except PaymentTransaction.DoesNotExist:
            return Response({'error': 'Транзакция не найдена.'}, status=status.HTTP_404_NOT_FOUND)

        if transaction.status == 'completed': # Избегаем повторной обработки
            return Response({'message': 'Транзакция уже обработана.'}, status=status.HTTP_200_OK)

        # Имитация обработки статуса
        if payment_status_gateway == 'payment.succeeded': # Заменить на реальный статус успеха
            transaction.status = 'completed'
            # Создаем UserPackage
            if transaction.package_purchased and transaction.user:
                user_package, created = UserPackage.objects.get_or_create(
                    user=transaction.user,
                    package=transaction.package_purchased,
                    # Можно добавить логику для предотвращения дублирования активных пакетов одного типа,
                    # или суммирования минут, если это предусмотрено
                    defaults={'minutes_remaining': transaction.package_purchased.minutes_amount}
                )
                if not created: # Если пакет уже существует (например, пользователь покупает такой же снова)
                    user_package.minutes_remaining += transaction.package_purchased.minutes_amount
                    user_package.is_active = True
                    user_package.save()
                
                transaction.user_package_created = user_package
            # Здесь можно отправить email/уведомление пользователю
            transaction.raw_response_gateway = str(payload) # Сохраняем ответ шлюза
            transaction.save()
            return Response({'message': 'Платеж успешно обработан.'}, status=status.HTTP_200_OK)
        
        elif payment_status_gateway == 'payment.failed': # Заменить на реальный статус ошибки
            transaction.status = 'failed'
            transaction.raw_response_gateway = str(payload)
            transaction.save()
            return Response({'message': 'Ошибка платежа.'}, status=status.HTTP_200_OK) # Шлюз ожидает 200 OK
        
        # Другие статусы...

        return Response({'message': 'Уведомление получено, статус не изменился.'}, status=status.HTTP_200_OK)

# Можно добавить представления для просмотра статуса платежа пользователем,
# истории транзакций и т.д.