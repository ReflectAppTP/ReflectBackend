from rest_framework import serializers
from .models import *
from django.utils import timezone

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
        read_only_fields = ['id', 'created_at', 'tags', 'emotional_tags']

    def create(self, validated_data):

        validated_data.pop('created_at', None)
        validated_data['created_at'] = timezone.localtime(timezone.now())
        tags = validated_data.pop('tags', [])
        emotional_tags = validated_data.pop('emotional_tags', [])

        user_state = UserState.objects.create(**validated_data)

        user_state.tags.set(tags)
        user_state.emotional_tags.set(emotional_tags)

        return user_state