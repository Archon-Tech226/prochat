from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Sum, Count
from functools import wraps
from decouple import config
from accounts.models import UserProfile
from payments.models import Payment, Subscription


# ── Owner Required Decorator ──────────────────────────────────────────────────
def owner_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('owner_login')
        if not request.user.is_superuser:
            return redirect('owner_login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Owner Login ───────────────────────────────────────────────────────────────
def owner_login(request):
    # Already logged in as superuser
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('owner_dashboard')

    error = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if username and password:
            # Read from .env — never hardcode!
            owner_username = config('OWNER_USERNAME', default='')
            owner_password = config('OWNER_PASSWORD', default='')

            if username == owner_username and password == owner_password:
                # Authenticate via Django auth
                user = authenticate(request, username=username, password=password)
                if user is not None and user.is_superuser:
                    auth_login(request, user)
                    return redirect('owner_dashboard')
                else:
                    error = 'Access denied. Not a superuser account.'
            else:
                error = 'Invalid username or password.'
        else:
            error = 'Please enter both username and password.'

    return render(request, 'owner/login.html', {'error': error})


# ── Owner Logout ──────────────────────────────────────────────────────────────
def owner_logout(request):
    auth_logout(request)
    return redirect('owner_login')


# ── Dashboard ─────────────────────────────────────────────────────────────────
@owner_required
def dashboard(request):
    total_users     = User.objects.count()
    active_subs     = Subscription.objects.filter(status='active').count()
    trial_users     = UserProfile.objects.filter(plan='free_trial').count()
    total_revenue   = Payment.objects.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    failed_payments = Payment.objects.filter(status='failed').count()

    context = {
        'total_users':     total_users,
        'active_subs':     active_subs,
        'trial_users':     trial_users,
        'total_revenue':   total_revenue,
        'failed_payments': failed_payments,
    }
    return render(request, 'owner/dashboard.html', context)


# ── Users List ────────────────────────────────────────────────────────────────
@owner_required
def user_list(request):
    search = request.GET.get('search', '')
    plan   = request.GET.get('plan', '')
    role   = request.GET.get('role', '')

    profiles = UserProfile.objects.select_related('user').all()

    if search:
        profiles = profiles.filter(user__email__icontains=search)
    if plan:
        profiles = profiles.filter(plan=plan)
    if role:
        profiles = profiles.filter(role=role)

    return render(request, 'owner/users.html', {'profiles': profiles})


# ── User Detail ───────────────────────────────────────────────────────────────
@owner_required
def user_detail(request, user_id):
    user     = get_object_or_404(User, id=user_id)
    profile  = user.userprofile
    payments = Payment.objects.filter(user=user).order_by('-created_at')

    if request.method == 'POST':
        new_plan = request.POST.get('plan')
        if new_plan:
            profile.plan = new_plan
            profile.save()

    return render(request, 'owner/user_detail.html', {
        'profile':  profile,
        'payments': payments,
    })


# ── Payment List ──────────────────────────────────────────────────────────────
@owner_required
def payment_list(request):
    payments = Payment.objects.select_related('user').order_by('-created_at')
    return render(request, 'owner/payments.html', {'payments': payments})


# ── Refund Payment ────────────────────────────────────────────────────────────
@owner_required
def refund_payment(request, payment_id):
    if request.method == 'POST':
        payment = get_object_or_404(Payment, id=payment_id)
        from django.conf import settings
        import razorpay
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        client.payment.refund(payment.razorpay_payment_id, {
            'amount': int(payment.amount * 100)
        })
        payment.status = 'refunded'
        payment.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'POST required'}, status=400)


# ── Subscription List ─────────────────────────────────────────────────────────
@owner_required
def subscription_list(request):
    subscriptions = Subscription.objects.select_related('user').order_by('-created_at')
    return render(request, 'owner/subscriptions.html', {'subscriptions': subscriptions})


# ── Analytics ─────────────────────────────────────────────────────────────────
@owner_required
def analytics(request):
    plan_counts = UserProfile.objects.values('plan').annotate(count=Count('id'))
    role_counts = UserProfile.objects.values('role').annotate(count=Count('id'))

    return render(request, 'owner/analytics.html', {
        'plan_counts': plan_counts,
        'role_counts': role_counts,
    })