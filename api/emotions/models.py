from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    emoji = models.CharField(max_length=10, blank=True, null=True)

class EmotionalTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    emoji = models.CharField(max_length=10, blank=True, null=True)


class UserState(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False,  # Должно быть False
        related_name='states'
    )
    description = models.TextField(blank=True)
    value = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    tags = models.ManyToManyField(Tag, through='UserStateTag', related_name='user_states')
    emotional_tags = models.ManyToManyField(EmotionalTag, through='UserEmotionalTag', related_name='user_states')


class UserStateTag(models.Model):
    user_state = models.ForeignKey(UserState, on_delete=models.CASCADE, related_name='state_tags')
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user_state', 'tag')

class UserEmotionalTag(models.Model):
    user_state = models.ForeignKey(UserState, on_delete=models.CASCADE, related_name='emotional_tag_relations')
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