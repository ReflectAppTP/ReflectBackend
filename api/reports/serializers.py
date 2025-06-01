from rest_framework import serializers
from .models import StateReport, UserReport
from django.contrib.auth import get_user_model
from .models import UserState  # путь укажи свой

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
