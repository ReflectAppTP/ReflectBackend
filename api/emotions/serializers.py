from rest_framework import serializers
from .models import *


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class EmotionalTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmotionalTag
        fields = '__all__'


class UserStateSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    emotional_tags = EmotionalTagSerializer(many=True, read_only=True)

    class Meta:
        model = UserState
        fields = ['id', 'user', 'value', 'description', 'created_at', 'tags', 'emotional_tags']


class CreateUserStateSerializer(serializers.ModelSerializer):
    tag_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    emotional_tag_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)

    class Meta:
        model = UserState
        fields = ['value', 'description', 'tag_ids', 'emotional_tag_ids']

    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        emotional_tag_ids = validated_data.pop('emotional_tag_ids', [])
        user_state = UserState.objects.create(user=self.context['request'].user, **validated_data)

        for tag_id in tag_ids:
            UserStateTag.objects.create(user_state=user_state, tag_id=tag_id)

        for emotional_tag_id in emotional_tag_ids:
            UserEmotionalTag.objects.create(user_state=user_state, emotional_tag_id=emotional_tag_id)

        return user_state