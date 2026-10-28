from django.db import models
from django.contrib.auth.models import User


class Task(models.Model):
    STATUS_CHOICES = [
        ('todo',        'To Do'),
        ('in_progress', 'In Progress'),
        ('done',        'Done'),
        ('overdue',     'Overdue'),
    ]
    PRIORITY_CHOICES = [
        ('low',    'Low'),
        ('medium', 'Medium'),
        ('high',   'High'),
        ('urgent', 'Urgent'),
    ]

    owner        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title        = models.CharField(max_length=200)
    description  = models.TextField(blank=True)
    due_date     = models.DateField(null=True, blank=True, db_index=True)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority     = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    ai_suggested = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date', '-priority']

    def __str__(self):
        return self.title