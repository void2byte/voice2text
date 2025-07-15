from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User # Используем реальную модель User
from .models import MinutePackage, PurchaseHistory # Используем реальные модели
from .forms import MinutePackageForm
from django.db.models import Sum, Count # Для агрегации данных

# Декоратор для проверки, является ли пользователь администратором (staff status)
def is_admin(user):
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(is_admin)
def manage_users(request):
    users = User.objects.all().prefetch_related('profile') # Оптимизация, если есть UserProfile
    return render(request, 'admin_panel/manage_users.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def manage_minute_packages(request):
    packages = MinutePackage.objects.all()
    # Форма для добавления нового пакета может быть передана здесь, если она отображается на той же странице
    # form = MinutePackageForm() 
    # context = {'packages': packages, 'form': form}
    context = {'packages': packages}
    return render(request, 'admin_panel/manage_packages.html', context)

@login_required
@user_passes_test(is_admin)
def add_minute_package(request):
    if request.method == 'POST':
        form = MinutePackageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Minute package added successfully!')
            return redirect(reverse('admin_panel:manage_packages'))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MinutePackageForm()
    return render(request, 'admin_panel/add_edit_package.html', {'form': form, 'action_name': 'Add'})

@login_required
@user_passes_test(is_admin)
def edit_minute_package(request, package_id):
    package = get_object_or_404(MinutePackage, pk=package_id)
    if request.method == 'POST':
        form = MinutePackageForm(request.POST, instance=package)
        if form.is_valid():
            form.save()
            messages.success(request, f'Package "{package.name}" updated successfully!')
            return redirect(reverse('admin_panel:manage_packages'))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MinutePackageForm(instance=package)
    return render(request, 'admin_panel/add_edit_package.html', {'form': form, 'package': package, 'action_name': 'Edit'})

@login_required
@user_passes_test(is_admin)
def delete_minute_package(request, package_id):
    package = get_object_or_404(MinutePackage, pk=package_id)
    if request.method == 'POST':
        package_name = package.name
        try:
            package.delete()
            messages.success(request, f'Package "{package_name}" deleted successfully!')
        except Exception as e: # Обработка возможных ошибок при удалении (например, связанных объектов)
            messages.error(request, f'Error deleting package "{package_name}": {e}')
        return redirect(reverse('admin_panel:manage_packages'))
    
    return render(request, 'admin_panel/confirm_delete_package.html', {'package': package})

@login_required
@user_passes_test(is_admin)
def view_statistics(request):
    total_users = User.objects.count()
    active_users_count = User.objects.filter(is_active=True).count()
    total_packages_count = MinutePackage.objects.count()
    
    # Статистика по продажам из PurchaseHistory
    total_revenue = PurchaseHistory.objects.aggregate(total=Sum('price_at_purchase'))['total'] or 0
    total_packages_sold = PurchaseHistory.objects.count()
    
    # Можно добавить более сложную статистику, например, самые популярные пакеты
    # popular_packages = PurchaseHistory.objects.values('package__name').annotate(count=Count('package')).order_by('-count')

    context = {
        'total_users': total_users,
        'active_users': active_users_count,
        'total_packages_available': total_packages_count,
        'total_revenue': total_revenue,
        'total_packages_sold': total_packages_sold,
        # 'popular_packages': popular_packages 
    }
    return render(request, 'admin_panel/view_statistics.html', context)

# from flask import render_template, request, redirect, url_for, flash
# from flask_login import login_required, current_user
# # ... Flask-специфичные декораторы и логика ...