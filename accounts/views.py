
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import secrets
import string

from .models import UserProfile, OTPVerification


# Home
def home(request):
    if request.user.is_authenticated:
        return redirect('workspace')
    return redirect('login')


# Login: send OTP
def login_view(request):
    if request.user.is_authenticated:
        return redirect('workspace')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()

        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'accounts/login.html')

        # Generate a six-digit OTP
        otp = ''.join(secrets.choice(string.digits) for _ in range(6))

        # Remove previous unused OTPs for this email
        OTPVerification.objects.filter(
            email=email,
            is_used=False
        ).update(is_used=True)

        # Save the new OTP
        OTPVerification.objects.create(
            email=email,
            otp=otp
        )

        try:
            send_mail(
                subject='Your ProChat OTP',
                message=(
                    f'Hi there!\n\n'
                    f'Your ProChat login OTP is: {otp}\n\n'
                    f'This OTP is valid for 10 minutes.\n\n'
                    f'If you did not request this, please ignore this email.\n\n'
                    f'Team ProChat'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception:
            # Log the actual exception in the terminal, not to the user
            import logging
            logging.getLogger(__name__).exception(
                'Failed to send ProChat OTP email'
            )
            messages.error(
                request,
                'Could not send the OTP. Please try again.'
            )
            return render(request, 'accounts/login.html')

        # Store the email in the session for the verification page
        request.session['otp_email'] = email
        request.session.set_expiry(600)
        request.session.modified = True

        # Redirect to the OTP entry page
        return redirect('verify_otp')

    return render(request, 'accounts/login.html')


# Verify OTP
def verify_otp(request):
    if request.user.is_authenticated:
        return redirect('workspace')

    email = request.session.get('otp_email')

    if not email:
        messages.error(
            request,
            'Please request an OTP first.'
        )
        return redirect('login')

    if request.method == 'POST':
        otp = request.POST.get('otp', '').strip()

        verification = (
            OTPVerification.objects
            .filter(
                email=email,
                otp=otp,
                is_used=False
            )
            .order_by('-id')
            .first()
        )

        if not verification:
            messages.error(request, 'Invalid OTP. Please try again.')
            return render(
                request,
                'accounts/verify_otp.html',
                {'email': email}
            )

        if verification.is_expired():
            verification.is_used = True
            verification.save(update_fields=['is_used'])
            request.session.pop('otp_email', None)
            messages.error(
                request,
                'Your OTP has expired. Please request a new one.'
            )
            return redirect('login')

        # Mark OTP as used
        verification.is_used = True
        verification.save(update_fields=['is_used'])

        # Find or create the user
        user = User.objects.filter(email__iexact=email).first()

        if user is None:
            base_username = email.split('@')[0]
            username = base_username
            counter = 1

            while User.objects.filter(username=username).exists():
                username = f'{base_username}{counter}'
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=email
            )
            created = True
        else:
            created = False

        # Get or create user profile
        profile, _ = UserProfile.objects.get_or_create(user=user)

        # Clear OTP session and log in
        request.session.pop('otp_email', None)
        login(
            request,
            user,
            backend='django.contrib.auth.backends.ModelBackend'
        )

        # New users or users without a role must select one
        if created or not profile.role:
            return redirect('role_select')

        return redirect('workspace')

    return render(
        request,
        'accounts/verify_otp.html',
        {'email': email}
    )


# Role selection
@login_required
def role_select(request):
    if request.method == 'POST':
        role = request.POST.get('role')

        if role in ['student', 'freelancer', 'worker', 'company']:
            profile, _ = UserProfile.objects.get_or_create(
                user=request.user
            )
            profile.role = role
            profile.save()
            return redirect('workspace')

        messages.error(request, 'Please select a valid role.')

    return render(request, 'accounts/role_select.html')


# Change role
@login_required
def change_role(request):
    if request.method == 'POST':
        role = request.POST.get('role')

        if role in ['student', 'freelancer', 'worker', 'company']:
            profile, _ = UserProfile.objects.get_or_create(
                user=request.user
            )
            profile.role = role
            profile.save()
            messages.success(
                request,
                f'Role changed to {role.title()} successfully!'
            )
            return redirect('workspace')

        messages.error(request, 'Please select a valid role.')

    return render(request, 'accounts/role_select.html')


# Workspace
@login_required
def workspace(request):
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user
    )

    if not profile.role:
        return redirect('role_select')

    if profile.is_trial_expired() and profile.plan == 'free_trial':
        profile.plan = 'expired'
        profile.save()

    if profile.plan == 'expired':
        return redirect('paywall')

    context = {
        'profile': profile,
        'trial_days_remaining': profile.trial_days_remaining(),
    }
    return render(request, 'accounts/workspace.html', context)


# Settings
@login_required
def user_settings(request):
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':
        profile.bio = request.POST.get('bio', '')
        profile.phone = request.POST.get('phone', '')

        if request.FILES.get('avatar'):
            profile.avatar = request.FILES['avatar']

        profile.save()
        messages.success(request, 'Settings saved!')

    return render(
        request,
        'accounts/settings.html',
        {'profile': profile}
    )


# Logout
def logout_view(request):
    logout(request)
    return redirect('login')


# Paywall
@login_required
def paywall(request):
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user
    )
    return render(
        request,
        'payments/paywall.html',
        {'profile': profile}
    )


# 404 handler
def handler404(request, exception):
    return render(request, '404.html', status=404)
