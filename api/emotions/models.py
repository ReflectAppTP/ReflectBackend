from django.db import models
from api.authReflect.models import User

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    emoji = models.CharField(max_length=10, blank=True, null=True)

class EmotionalTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    emoji = models.CharField(max_length=10, blank=True, null=True)

class UserState(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class UserStateTag(models.Model):
    user_state = models.ForeignKey('UserState', on_delete=models.CASCADE)
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user_state', 'tag')

class UserEmotionalTag(models.Model):
    user_state = models.ForeignKey('UserState', on_delete=models.CASCADE)
    emotional_tag = models.ForeignKey('EmotionalTag', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user_state', 'emotional_tag')

class Friend(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friends1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friends2')
    is_accepted_user1 = models.BooleanField(default=False)
    is_accepted_user2 = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user1', 'user2')
        constraints = [
            models.CheckConstraint(
                check=models.Q(user1_id__lt=models.F('user2_id')),
                name='user1_lt_user2'
            )
        ]