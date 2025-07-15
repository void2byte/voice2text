from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

class UserAdmin(BaseUserAdmin):
    # Добавьте 'telegram_id' и другие кастомные поля в списки для отображения и редактирования в админке
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'telegram_id')
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('telegram_id',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('telegram_id',)}),
    )

admin.site.register(User, UserAdmin)