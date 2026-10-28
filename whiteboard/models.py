from django.db import models
from django.contrib.auth.models import User


class Board(models.Model):
    name       = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='boards')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class BoardStroke(models.Model):
    board      = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='strokes')
    user       = models.ForeignKey(User, on_delete=models.CASCADE)
    stroke_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)