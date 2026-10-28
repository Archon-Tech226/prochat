from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from .models import Group, Channel, Message, DirectMessage, GroupInvite


@login_required
def group_list(request):
    groups    = request.user.chat_groups.all()
    all_users = User.objects.exclude(id=request.user.id)
    return render(request, 'chat/group_list.html', {
        'groups':    groups,
        'all_users': all_users,
    })


@login_required
def channel_view(request, channel_id):
    channel       = get_object_or_404(Channel, id=channel_id)
    messages_list = Message.objects.filter(channel=channel, is_deleted=False).order_by('created_at')[:50]
    return render(request, 'chat/chat_room.html', {
        'channel':  channel,
        'messages': messages_list,
    })


@login_required
def dm_view(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    dms = DirectMessage.objects.filter(
        sender__in=[request.user, other_user],
        receiver__in=[request.user, other_user],
        is_deleted=False
    ).order_by('created_at')[:50]
    return render(request, 'chat/dm.html', {
        'other_user': other_user,
        'messages':   dms,
    })


@login_required
def dm_list(request):
    """Show all users to DM"""
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'chat/dm_list.html', {'users': users})


@login_required
def create_group(request):
    if request.method == 'POST':
        name       = request.POST.get('name')
        group_type = request.POST.get('group_type', 'project')
        is_public  = request.POST.get('is_public') == 'on'

        group = Group.objects.create(
            name=name,
            group_type=group_type,
            created_by=request.user,
            is_public=is_public
        )
        group.members.add(request.user)
        Channel.objects.create(group=group, name='general')
        messages.success(request, f'Team "{name}" created!')
        return redirect('group_detail', group_id=group.id)

    return render(request, 'chat/create_group.html')


@login_required
def group_detail(request, group_id):
    group      = get_object_or_404(Group, id=group_id)
    members    = group.members.all()
    invite, _  = GroupInvite.objects.get_or_create(
        group=group, created_by=request.user, is_active=True
    )
    invite_url = request.build_absolute_uri(f'/chat/join/{invite.token}/')

    return render(request, 'chat/group_detail.html', {
        'group':      group,
        'members':    members,
        'invite_url': invite_url,
        'invite':     invite,
    })


@login_required
def get_invite_link(request, group_id):
    """API endpoint for invite link"""
    group     = get_object_or_404(Group, id=group_id)
    invite, _ = GroupInvite.objects.get_or_create(
        group=group, created_by=request.user, is_active=True
    )
    invite_url = request.build_absolute_uri(f'/chat/join/{invite.token}/')
    return JsonResponse({'invite_url': invite_url})


@login_required
def add_member_by_email(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    if group.created_by != request.user:
        messages.error(request, 'Only the group creator can add members.')
        return redirect('group_list')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        try:
            user = User.objects.get(email=email)
            if group.members.filter(id=user.id).exists():
                messages.warning(request, f'{email} is already a member!')
            else:
                group.members.add(user)

                # Send notification
                try:
                    from notifications.models import Notification
                    from channels.layers import get_channel_layer
                    from asgiref.sync import async_to_sync

                    notif = Notification.objects.create(
                        user=user,
                        title=f'Added to {group.name}',
                        body=f'{request.user.username} added you to {group.name}',
                        notif_type='message',
                        link=f'/chat/group/{group.id}/',
                    )

                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f'notifications_{user.id}',
                        {
                            'type':       'send_notification',
                            'title':      notif.title,
                            'body':       notif.body,
                            'notif_type': 'message',
                            'link':       notif.link,
                        }
                    )
                except Exception:
                    pass

                messages.success(request, f'{user.username} added successfully!')
        except User.DoesNotExist:
            messages.error(request, f'No user found with email: {email}')

    return redirect('group_list')


@login_required
def remove_member(request, group_id, user_id):
    group = get_object_or_404(Group, id=group_id)
    if group.created_by != request.user:
        return redirect('group_list')
    user = get_object_or_404(User, id=user_id)
    if user != group.created_by:
        group.members.remove(user)
    return redirect('group_detail', group_id=group_id)


@login_required
def join_via_invite(request, token):
    invite = get_object_or_404(GroupInvite, token=token, is_active=True)
    group  = invite.group
    if not group.members.filter(id=request.user.id).exists():
        group.members.add(request.user)
        messages.success(request, f'You joined {group.name}!')
    return redirect('group_detail', group_id=group.id)


@login_required
def regenerate_invite(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if group.created_by == request.user:
        GroupInvite.objects.filter(group=group).update(is_active=False)
        GroupInvite.objects.create(group=group, created_by=request.user)
    return redirect('group_detail', group_id=group_id)


@login_required
def leave_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if group.created_by != request.user:
        group.members.remove(request.user)
    return redirect('group_list')


@login_required
def create_channel(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.method == 'POST':
        Channel.objects.create(group=group, name=request.POST.get('name'))
        return redirect('group_detail', group_id=group_id)
    return render(request, 'chat/create_channel.html', {'group': group})