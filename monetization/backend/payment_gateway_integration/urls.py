from django.urls import path
from .views import InitiatePaymentView, PaymentWebhookView

urlpatterns = [
    path('initiate/', InitiatePaymentView.as_view(), name='initiate_payment'),
    path('webhook/', PaymentWebhookView.as_view(), name='payment_webhook'), # URL для коллбэков от платежной системы
    # path('success/', PaymentSuccessView.as_view(), name='payment_success_callback'), # Пример URL для редиректа после успешной оплаты
    # path('fail/', PaymentFailView.as_view(), name='payment_fail_callback'),       # Пример URL для редиректа после неудачной оплаты
]