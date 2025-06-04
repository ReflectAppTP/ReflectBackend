from rest_framework import serializers
from .models import StateReport, UserReport
from django.contrib.auth import get_user_model

User = get_user_model()

class StateReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = StateReport
        fields = '__all__'
        read_only_fields = ['reporter', 'created_at', 'is_resolved', 'is_accepted']

class UserReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserReport
        fields = '__all__'
        read_only_fields = ['reporter', 'created_at', 'is_resolved', 'is_accepted']

class BlockUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['is_blocked']

class AdminUsernameSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username']

class AdminBlockStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['is_blocked']

class AdminPrivilegesSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['is_admin']