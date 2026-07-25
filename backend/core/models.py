from django.conf import settings
from django.db import models

from ponds.models import Pond


class Notification(models.Model):
    class Priority(models.TextChoices):
        HIGH = 'High', 'High'
        MEDIUM = 'Medium', 'Medium'
        LOW = 'Low', 'Low'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    pond = models.ForeignKey(
        Pond,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    parameter = models.CharField(max_length=80)
    current_value = models.CharField(max_length=80)
    reason = models.TextField()
    priority = models.CharField(
        max_length=16,
        choices=Priority.choices,
        default=Priority.LOW,
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.priority}: {self.parameter} in {self.pond}'
