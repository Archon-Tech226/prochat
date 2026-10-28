from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('student',    'Student'),
        ('freelancer', 'Freelancer'),
        ('worker',     'Worker'),
        ('company',    'Company'),
    ]

    PLAN_CHOICES = [
        ('free_trial', 'Free Trial'),
        ('pro',        'Pro'),
        ('team',       'Team'),
        ('company',    'Company'),
        ('expired',    'Expired'),
    ]

    user             = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    role             = models.CharField(max_length=20, choices=ROLE_CHOICES, default='', blank=True)
    plan             = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free_trial')
    trial_start_date = models.DateField(default=date.today)
    avatar           = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio              = models.TextField(blank=True)
    phone            = models.CharField(max_length=15, blank=True)
    is_online        = models.BooleanField(default=False)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.role} - {self.plan}"

    def trial_days_remaining(self):
        from django.conf import settings
        trial_days = getattr(settings, 'TRIAL_DAYS', 15)
        end_date   = self.trial_start_date + timedelta(days=trial_days)
        remaining  = (end_date - date.today()).days
        return max(0, remaining)

    def is_trial_expired(self):
        return self.trial_days_remaining() == 0

    def has_access(self):
        return self.plan != 'expired'


class OTPVerification(models.Model):
    email      = models.EmailField()
    otp        = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used    = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.email} - {self.otp}"

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)