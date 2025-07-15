# urls.py or routes.py for admin_panel

# urls.py for admin_panel

from django.urls import path
from . import views

app_name = 'admin_panel'  # Пространство имен для URL

urlpatterns = [
    # URL для управления пользователями
    path('users/', views.manage_users, name='manage_users'),

    # URL для управления пакетами минут
    path('packages/', views.manage_minute_packages, name='manage_packages'),
    path('packages/add/', views.add_minute_package, name='add_package'),
    path('packages/edit/<int:package_id>/', views.edit_minute_package, name='edit_package'),
    path('packages/delete/<int:package_id>/', views.delete_minute_package, name='delete_package'),

    # URL для просмотра статистики
    path('statistics/', views.view_statistics, name='view_statistics'),

    # Возможно, главный URL для админ-панели (если есть)
    # path('', views.admin_dashboard, name='admin_dashboard'), # Предполагая, что есть такое представление
]


# --- Flask Example --- 
# from flask import Blueprint
# from . import views # Ensure views are correctly imported based on your project structure
# 
# admin_bp = Blueprint('admin_panel', __name__, template_folder='../templates/admin_panel', url_prefix='/admin') # Adjusted template_folder path
# 
# @admin_bp.route('/')
# def dashboard():
#     # return views.admin_dashboard() # Placeholder for a potential dashboard view
#     return "Admin Dashboard Placeholder - Flask"
# 
# @admin_bp.route('/users')
# def manage_users_route():
#     return views.manage_users()
# 
# @admin_bp.route('/packages', methods=['GET', 'POST']) # Allow POST for form submission
# def manage_packages_route():
#     return views.manage_minute_packages()
# 
# @admin_bp.route('/packages/add', methods=['GET', 'POST'])
# def add_package_route():
#     return views.add_minute_package()
# 
# @admin_bp.route('/packages/edit/<int:package_id>', methods=['GET', 'POST'])
# def edit_package_route(package_id):
#     return views.edit_minute_package(package_id)
# 
# @admin_bp.route('/packages/delete/<int:package_id>', methods=['POST']) # Typically POST for delete actions
# def delete_package_route(package_id):
#     return views.delete_minute_package(package_id)
# 
# @admin_bp.route('/statistics') # Changed 'stats' to 'statistics'
# def view_statistics_route():
#     return views.view_statistics()

# To register the blueprint in your main Flask app (e.g., app.py or __init__.py):
# from monetization.backend.admin_panel.urls import admin_bp # Adjust import path as necessary
# app.register_blueprint(admin_bp)