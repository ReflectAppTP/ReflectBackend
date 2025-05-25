from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class DeepSeekAnalysis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    correlation_id = models.CharField(max_length=36, unique=True)
    input_data = models.JSONField()  # Входные данные (эмоции, теги)
    output_result = models.JSONField(null=True)  # Ответ от DeepSeek
    status = models.CharField(max_length=20, default='processing')  # processing/completed/failed
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'ai'
        indexes = [
            models.Index(fields=['correlation_id']),
            models.Index(fields=['user', 'status']),
        ]


class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.UUIDField(default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'ai_chatsession'

class ChatMessage(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('failed', 'Failed')
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    content = models.TextField()
    role = models.CharField(max_length=10, choices=[('user', 'User'), ('assistant', 'Assistant')])
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
        ]