from rest_framework import serializers
from .models import Friendship
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']  # Добавьте нужные поля


class FriendshipSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)

    class Meta:
        model = Friendship
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class CreateFriendshipSerializer(serializers.ModelSerializer):
    to_user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Friendship
        fields = ['to_user_id', 'status']
        read_only_fields = ['status']


class UpdateFriendshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friendship
        fields = ['status']