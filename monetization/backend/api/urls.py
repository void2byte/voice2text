from django.urls import path
from .views import user_profile_with_balance, spend_minutes_api

app_name = 'api'

urlpatterns = [
    path('profile/', user_profile_with_balance, name='user_profile_with_balance'),
    path('spend_minutes/', spend_minutes_api, name='spend_minutes_api'),
    # Другие URL-маршруты для общих API эндпоинтов
]