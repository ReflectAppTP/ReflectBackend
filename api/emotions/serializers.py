from rest_framework import serializers
from .models import *

class EmotionalTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmotionalTag
        fields = ['id', 'name', 'emoji']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'emoji']


class UserStateSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    emotional_tags = EmotionalTagSerializer(many=True, read_only=True)

    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        source='tags',
        write_only=True,
        required=False
    )
    emotional_tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=EmotionalTag.objects.all(),
        source='emotional_tags',
        write_only=True,
        required=False
    )

    class Meta:
        model = UserState
        fields = [
            'id',
            'description',
            'value',
            'created_at',
            'tags',
            'emotional_tags',
            'tag_ids',
            'emotional_tag_ids'
        ]
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        # Убедимся, что created_at не передается
        validated_data.pop('created_at', None)

        tags = validated_data.pop('tags', [])
        emotional_tags = validated_data.pop('emotional_tags', [])

        # Пользователь уже в validated_data благодаря perform_create
        user_state = UserState.objects.create(**validated_data)

        user_state.tags.set(tags)
        user_state.emotional_tags.set(emotional_tags)

        return user_state