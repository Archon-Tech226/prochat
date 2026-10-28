from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    NOTIF_TYPES = [
        ('message',  'Message'),
        ('meeting',  'Meeting'),
        ('task',     'Task'),
        ('payment',  'Payment'),
        ('system',   'System'),
    ]
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', db_index=True)
    title      = models.CharField(max_length=200)
    body       = models.TextField()
    notif_type = models.CharField(max_length=20, choices=NOTIF_TYPES, default='system')
    is_read    = models.BooleanField(default=False)
    link       = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} — {self.title}"