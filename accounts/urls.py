
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('role-select/', views.role_select, name='role_select'),
    path('change-role/', views.change_role, name='change_role'),
    path('workspace/', views.workspace, name='workspace'),
    path('settings/', views.user_settings, name='settings'),
    path('logout/', views.logout_view, name='logout'),
    path('plans/', views.paywall, name='paywall'),
]
