from django.db import models
from django.contrib.auth.models import User


class UploadedFile(models.Model):
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    file        = models.FileField(upload_to='uploads/%Y/%m/%d/')
    file_name   = models.CharField(max_length=255)
    file_type   = models.CharField(max_length=50, blank=True)
    file_size   = models.PositiveIntegerField(default=0)
    thumbnail   = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.file_name