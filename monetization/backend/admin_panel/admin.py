from django.contrib import admin
from .models import MinutePackage, UserProfile, PurchaseHistory

@admin.register(MinutePackage)
class MinutePackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'minutes', 'price', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('price',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at') # Добавьте сюда 'remaining_minutes', 'telegram_id', если они будут в модели
    search_fields = ('user__username', 'user__email') # Поиск по полям связанной модели User
    # list_select_related = ('user',) # Оптимизация запросов, если часто обращаетесь к user

@admin.register(PurchaseHistory)
class PurchaseHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'package_name', 'purchase_date', 'price_at_purchase', 'minutes_at_purchase')
    list_filter = ('purchase_date', 'package')
    search_fields = ('user__username', 'package__name')
    date_hierarchy = 'purchase_date'
    list_select_related = ('user', 'package') # Оптимизация запросов

    def package_name(self, obj):
        return obj.package.name if obj.package else "N/A"
    package_name.short_description = 'Package Name'