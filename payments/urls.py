from django.urls import path
from . import views

urlpatterns = [
    path('',              views.paywall,          name='paywall'),
    path('create-order/', views.create_order,     name='create_order'),
    path('webhook/',      views.payment_webhook,  name='payment_webhook'),
    path('success/',      views.payment_success,  name='payment_success'),
    path('history/',      views.payment_history,  name='payment_history'),
]