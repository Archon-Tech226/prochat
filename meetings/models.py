import uuid
from django.db import models
from django.contrib.auth.models import User


class Meeting(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title        = models.CharField(max_length=200)
    host         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_meetings')
    attendees    = models.ManyToManyField(User, related_name='meetings', blank=True)
    scheduled_at = models.DateTimeField()
    ended_at     = models.DateTimeField(null=True, blank=True)
    transcript   = models.TextField(blank=True)
    summary      = models.TextField(blank=True)
    action_items = models.JSONField(default=list)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def is_active(self):
        return self.ended_at is None