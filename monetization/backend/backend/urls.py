from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user_management/', include('user_management.urls')),
    path('api/minute_package_management/', include('minute_package_management.urls')),
    path('api/payment_gateway_integration/', include('payment_gateway_integration.urls')),
    path('api/v1/', include('api.urls')), # Общие API эндпоинты
    # path('admin_panel/', include('admin_panel.urls')), # Раскомментировать, когда будет готово
]