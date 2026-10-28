import uuid
from django.db import models
from django.contrib.auth.models import User


class Group(models.Model):
    GROUP_TYPES = [
        ('company',   'Company'),
        ('project',   'Project Team'),
        ('classroom', 'Classroom'),
        ('community', 'Community'),
    ]
    name        = models.CharField(max_length=100)
    group_type  = models.CharField(max_length=20, choices=GROUP_TYPES, default='project')
    created_by  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members     = models.ManyToManyField(User, related_name='chat_groups', blank=True)
    is_public   = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class GroupInvite(models.Model):
    group      = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='invites')
    token      = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.group.name} — {self.token}"

    def get_invite_url(self):
        return f"/chat/join/{self.token}/"


class Channel(models.Model):
    group       = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='channels')
    name        = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.group.name} → #{self.name}"


class Message(models.Model):
    channel    = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='messages')
    sender     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    content    = models.TextField()
    attachment = models.FileField(upload_to='chat_attachments/', blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"


class DirectMessage(models.Model):
    sender     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_dms')
    receiver   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_dms')
    content    = models.TextField()
    attachment = models.FileField(upload_to='dm_attachments/', blank=True, null=True)
    is_read    = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}: {self.content[:50]}"