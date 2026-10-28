from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Subscription, Payment
import razorpay
import json
import hmac
import hashlib


PLAN_PRICES = {
    'pro':     49900,   # ₹499 in paise
    'team':    149900,  # ₹1499 in paise
    'company': 499900,  # ₹4999 in paise
}


@login_required
def paywall(request):
    profile = request.user.userprofile
    return render(request, 'payments/paywall.html', {'profile': profile})


@login_required
def create_order(request):
    if request.method == 'POST':
        data   = json.loads(request.body)
        plan   = data.get('plan', 'pro')
        amount = PLAN_PRICES.get(plan, 49900)

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        order  = client.order.create({
            'amount':   amount,
            'currency': 'INR',
            'notes':    {'plan': plan, 'user_id': str(request.user.id)},
        })

        return JsonResponse({
            'order_id': order['id'],
            'amount':   amount,
            'key':      settings.RAZORPAY_KEY_ID,
            'plan':     plan,
        })

    return JsonResponse({'error': 'POST required'}, status=400)


@csrf_exempt
def payment_webhook(request):
    if request.method == 'POST':
        payload   = request.body
        signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE', '')

        # Verify signature
        expected = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected, signature):
            return JsonResponse({'error': 'Invalid signature'}, status=400)

        data  = json.loads(payload)
        event = data.get('event', '')

        if event == 'payment.captured':
            payment_data = data['payload']['payment']['entity']
            user_id      = payment_data.get('notes', {}).get('user_id')
            plan         = payment_data.get('notes', {}).get('plan', 'pro')

            if user_id:
                from django.contrib.auth.models import User
                try:
                    user = User.objects.get(id=user_id)

                    # Create payment record
                    Payment.objects.create(
                        user=user,
                        amount=payment_data['amount'] / 100,
                        razorpay_payment_id=payment_data['id'],
                        status='paid',
                        payment_method=payment_data.get('method', ''),
                    )

                    # Update user plan
                    user.userprofile.plan = plan
                    user.userprofile.save()

                except User.DoesNotExist:
                    pass

        return JsonResponse({'status': 'ok'})

    return JsonResponse({'error': 'POST required'}, status=400)


@login_required
def payment_success(request):
    return render(request, 'payments/success.html')


@login_required
def payment_history(request):
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'payments/history.html', {'payments': payments})