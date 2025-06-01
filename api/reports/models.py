from django.db import models
from django.contrib.auth import get_user_model
from api.emotions.models import UserState

User = get_user_model()

class StateReport(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="state_reports")
    state = models.ForeignKey(UserState, on_delete=models.CASCADE, related_name="reports")
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    is_accepted = models.BooleanField(null=True)

class UserReport(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_reports")
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="complaints_received")
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    is_accepted = models.BooleanField(null=True)
