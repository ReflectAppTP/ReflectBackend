from rest_framework import serializers
from .models import *

class UserStateSerializer(serializers.ModelSerializer):
    emotional_tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=EmotionalTag.objects.all(),
        write_only=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        write_only=True
    )

    class Meta:
        model = UserState
        fields = ['id', 'description', 'value', 'created_at', 'emotional_tags', 'tags']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        emotional_tags = validated_data.pop('emotional_tags', [])
        tags = validated_data.pop('tags', [])

        user_state = UserState.objects.create(
            user=self.context['request'].user,
            **validated_data
        )

        for et in emotional_tags:
            UserEmotionalTag.objects.create(user_state=user_state, emotional_tag=et)

        for t in tags:
            UserStateTag.objects.create(user_state=user_state, tag=t)

        return user_state

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['emotional_tags'] = [et.id for et in instance.emotional_tags.all()]
        representation['tags'] = [t.id for t in instance.tags.all()]
        return representation