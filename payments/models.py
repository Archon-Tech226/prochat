from django.db import models
from django.contrib.auth.models import User


class Plan(models.Model):
    name     = models.CharField(max_length=50)
    slug     = models.CharField(max_length=20, unique=True)
    price    = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    STATUS_CHOICES = [
        ('active',    'Active'),
        ('cancelled', 'Cancelled'),
        ('past_due',  'Past Due'),
        ('expired',   'Expired'),
    ]
    user                   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions', db_index=True)
    plan                   = models.CharField(max_length=20)
    status                 = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    razorpay_subscription_id = models.CharField(max_length=100, blank=True)
    current_period_start   = models.DateField(null=True, blank=True)
    current_period_end     = models.DateField(null=True, blank=True)
    created_at             = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.plan}"


class Payment(models.Model):
    STATUS_CHOICES = [
        ('paid',     'Paid'),
        ('failed',   'Failed'),
        ('refunded', 'Refunded'),
    ]
    user               = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments', db_index=True)
    subscription       = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    amount             = models.DecimalField(max_digits=10, decimal_places=2)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_order_id   = models.CharField(max_length=100, blank=True)
    status             = models.CharField(max_length=20, choices=STATUS_CHOICES, default='paid')
    payment_method     = models.CharField(max_length=50, blank=True)
    created_at         = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.user.username} — ₹{self.amount} — {self.status}"