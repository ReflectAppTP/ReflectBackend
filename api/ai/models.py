from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class DeepSeekAnalysis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    correlation_id = models.CharField(max_length=36, unique=True)
    input_data = models.JSONField()  # Входные данные (эмоции, теги)
    output_result = models.JSONField(null=True)  # Ответ от DeepSeek
    status = models.CharField(max_length=20, default='processing')  # processing/completed/failed
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['correlation_id']),
            models.Index(fields=['user', 'status']),
        ]


class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message_id = models.UUIDField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    content = models.TextField()
    response = models.TextField(null=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('processed', 'Processed'), ('failed', 'Failed')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']