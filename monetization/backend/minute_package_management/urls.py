from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MinutePackageViewSet, UserPackageViewSet

router = DefaultRouter()
router.register(r'available', MinutePackageViewSet, basename='minute-package-available')
router.register(r'my', UserPackageViewSet, basename='user-minute-package')

urlpatterns = [
    path('', include(router.urls)),
]