from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class VisibilityUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['visibility']

class VisibilityUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['visibility']

class UsernameUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username']

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value