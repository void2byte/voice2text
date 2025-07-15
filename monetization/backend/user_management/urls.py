from django.urls import path
from .views import RegisterView, UserProfileView
# Если будете использовать стандартные представления Django REST framework для токенов:
# from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    # path('login/', obtain_auth_token, name='auth_login'), # Пример для входа, если используется TokenAuthentication
    # Добавьте другие URL-маршруты по необходимости
]