from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task(bind=True, max_retries=3)
def send_otp_email(self, email, otp):
    try:
        send_mail(
            subject='Your ProChat OTP',
            message=f'''
Hi there!

Your ProChat login OTP is: {otp}

This OTP is valid for 10 minutes.

If you did not request this, please ignore this email.

Team ProChat
            ''',
            from_email=settings.EMAIL_HOST_USER or 'noreply@prochat.app',
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task
def send_welcome_email(user_id):
    from django.contrib.auth.models import User
    try:
        user = User.objects.get(id=user_id)
        send_mail(
            subject='Welcome to ProChat!',
            message=f'''
Hi {user.username}!

Welcome to ProChat — your universal AI-powered workspace.

Get started:
1. Complete your profile
2. Create or join a team
3. Try the AI assistant

Team ProChat
            ''',
            from_email=settings.EMAIL_HOST_USER or 'noreply@prochat.app',
            recipient_list=[user.email],
            fail_silently=True,
        )
    except User.DoesNotExist:
        pass


@shared_task
def check_trial_expiry():
    from .models import UserProfile
    from django.utils import timezone
    from datetime import timedelta

    today = timezone.now().date()

    # Day 10 reminder
    day10_profiles = UserProfile.objects.filter(
        plan='free_trial',
        trial_start_date=today - timedelta(days=10)
    )
    for profile in day10_profiles:
        send_mail(
            subject='ProChat Trial — 5 days remaining!',
            message=f'Hi {profile.user.username}, your ProChat trial ends in 5 days. Upgrade now to keep access!',
            from_email='noreply@prochat.app',
            recipient_list=[profile.user.email],
            fail_silently=True,
        )

    # Day 13 reminder
    day13_profiles = UserProfile.objects.filter(
        plan='free_trial',
        trial_start_date=today - timedelta(days=13)
    )
    for profile in day13_profiles:
        send_mail(
            subject='ProChat Trial — 2 days remaining!',
            message=f'Hi {profile.user.username}, your ProChat trial ends in 2 days. Upgrade now!',
            from_email='noreply@prochat.app',
            recipient_list=[profile.user.email],
            fail_silently=True,
        )

    # Day 15 — expire
    expired_profiles = UserProfile.objects.filter(
        plan='free_trial',
        trial_start_date__lte=today - timedelta(days=15)
    )
    expired_profiles.update(plan='expired')