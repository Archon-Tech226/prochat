from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from .models import Meeting


@login_required
def meeting_list(request):
    meetings = Meeting.objects.filter(attendees=request.user).order_by('-scheduled_at')
    return render(request, 'meetings/list.html', {'meetings': meetings})


@login_required
def create_meeting(request):
    if request.method == 'POST':
        title        = request.POST.get('title')
        scheduled_at = request.POST.get('scheduled_at')
        invite_emails = request.POST.get('invite_emails', '')

        meeting = Meeting.objects.create(
            title=title,
            host=request.user,
            scheduled_at=scheduled_at,
        )
        meeting.attendees.add(request.user)

        # ── Email Invite ──
        if invite_emails:
            emails = [e.strip() for e in invite_emails.split(',') if e.strip()]
            meeting_url = request.build_absolute_uri(f'/meetings/{meeting.id}/')

            for email in emails:
                try:
                    send_mail(
                        subject=f'You are invited to: {meeting.title}',
                        message=f'''Hi!

{request.user.username} has invited you to a meeting on ProChat.

Meeting: {meeting.title}
Time: {meeting.scheduled_at}

Join here: {meeting_url}

Team ProChat''',
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[email],
                        fail_silently=True,
                    )

                    # Add user to attendees if they exist
                    try:
                        invited_user = User.objects.get(email=email)
                        meeting.attendees.add(invited_user)

                        # Send in-app notification
                        from notifications.models import Notification
                        from channels.layers import get_channel_layer
                        from asgiref.sync import async_to_sync

                        notif = Notification.objects.create(
                            user=invited_user,
                            title=f'Meeting Invite: {meeting.title}',
                            body=f'{request.user.username} invited you to a meeting',
                            notif_type='meeting',
                            link=f'/meetings/{meeting.id}/',
                        )

                        # Push WebSocket notification
                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.group_send)(
                            f'notifications_{invited_user.id}',
                            {
                                'type':       'send_notification',
                                'title':      notif.title,
                                'body':       notif.body,
                                'notif_type': 'meeting',
                                'link':       notif.link,
                            }
                        )
                    except User.DoesNotExist:
                        pass

                except Exception as e:
                    print(f'Invite email error: {e}')

        messages.success(request, f'Meeting "{title}" created!')
        return redirect('meeting_room', meeting_id=meeting.id)

    # Get all users for invite suggestions
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'meetings/create.html', {'users': users})


@login_required
def meeting_room(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)
    meeting.attendees.add(request.user)
    return render(request, 'meetings/room.html', {'meeting': meeting})


@login_required
def meeting_summary(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)
    return render(request, 'meetings/summary.html', {'meeting': meeting})