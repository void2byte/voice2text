from django.contrib import admin
from .models import MinutePackage, UserPackage

@admin.register(MinutePackage)
class MinutePackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'minutes_amount', 'price', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

@admin.register(UserPackage)
class UserPackageAdmin(admin.ModelAdmin):
    list_display = ('user', 'package', 'purchase_date', 'minutes_remaining', 'is_active')
    list_filter = ('is_active', 'package')
    search_fields = ('user__username', 'package__name')
    readonly_fields = ('purchase_date',)
    # Можно добавить кастомные действия, например, для деактивации пакетов