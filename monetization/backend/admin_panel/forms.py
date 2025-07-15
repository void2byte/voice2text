from django import forms
from .models import MinutePackage

class MinutePackageForm(forms.ModelForm):
    class Meta:
        model = MinutePackage
        fields = ['name', 'minutes', 'price', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        # Пример дополнительной валидации, если нужно
        # Например, проверка на уникальность, если не используется unique=True в модели
        # или более сложная логика
        if len(name) < 3:
             raise forms.ValidationError("Package name must be at least 3 characters long.")
        return name

    def clean_minutes(self):
        minutes = self.cleaned_data.get('minutes')
        if minutes is not None and minutes <= 0:
            raise forms.ValidationError("Minutes must be a positive integer.")
        return minutes

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise forms.ValidationError("Price must be a positive number.")
        return price

        return name

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise forms.ValidationError("Price must be a positive value.")
        return price

# Можно добавить другие формы, например, для управления пользователями, если потребуется.
# class UserAdminForm(forms.ModelForm):
#     class Meta:
# model = User # Предполагаемая модель пользователя
# fields = ['username', 'email', 'is_active', 'is_staff'] # и т.д.