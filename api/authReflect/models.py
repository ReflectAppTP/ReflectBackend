from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ValidationError

def validate_no_spaces(value):
    if value.strip() != value or ' ' in value:
        raise ValidationError("Пробелы запрещены")

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        user = self.model(
            username=username,
            email=self.normalize_email(email),
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True, validators=[validate_no_spaces])
    password = models.CharField(max_length=256, validators=[validate_no_spaces])
    created_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    VISIBILITY_CHOICES = [
        ('all', 'Виден всем'),
        ('friends', 'Виден друзьям'),
        ('self', 'Только себе'),
    ]
    objects = UserManager()
    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default='all'
    )
    is_blocked = models.BooleanField(default=False)
    is_guest = models.BooleanField(default=False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.set_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username