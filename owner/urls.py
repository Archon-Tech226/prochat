from django.urls import path
from . import views

urlpatterns = [
    # Owner Auth
    path('login/',                       views.owner_login,       name='owner_login'),
    path('logout/',                      views.owner_logout,      name='owner_logout'),

    # Dashboard pages
    path('dashboard/',                   views.dashboard,         name='owner_dashboard'),
    path('users/',                       views.user_list,         name='owner_users'),
    path('users/<int:user_id>/',         views.user_detail,       name='owner_user_detail'),
    path('payments/',                    views.payment_list,      name='owner_payments'),
    path('payments/<int:payment_id>/refund/', views.refund_payment, name='owner_refund'),
    path('subscriptions/',               views.subscription_list, name='owner_subscriptions'),
    path('analytics/',                   views.analytics,         name='owner_analytics'),
]