from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'created_at', 'is_admin', 'is_premium']
        read_only_fields = ['id', 'created_at']

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=6)
    def validate_email(self, value):
        if value.strip() != value:
            raise serializers.ValidationError("Email не должен содержать пробелов по краям")
        if ' ' in value:
            raise serializers.ValidationError("Email не должен содержать пробелов внутри")
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Некорректный email")
        return value

    def validate_password(self, value):
        if value.strip() != value:
            raise serializers.ValidationError("Пароль не должен содержать пробелов по краям")
        if ' ' in value:
            raise serializers.ValidationError("Пароль не должен содержать пробелов внутри")
        if len(value) < 8:
            raise serializers.ValidationError("Пароль должен быть не менее 8 символов")
        return value
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):

        return User.objects.create_user(**validated_data)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    def validate_email(self, value):
        if value.strip() != value:
            raise serializers.ValidationError("Email не должен содержать пробелов по краям")
        if ' ' in value:
            raise serializers.ValidationError("Email не должен содержать пробелов внутри")
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Некорректный email")
        return value

    def validate_password(self, value):
        if value.strip() != value:
            raise serializers.ValidationError("Пароль не должен содержать пробелов по краям")
        if ' ' in value:
            raise serializers.ValidationError("Пароль не должен содержать пробелов внутри")
        return value
