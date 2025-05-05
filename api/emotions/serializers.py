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

    # Поля для записи (принимают ID)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        source='tags',
        write_only=True
    )
    emotional_tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=EmotionalTag.objects.all(),
        source='emotional_tags',
        write_only=True
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
        tags = validated_data.pop('tags', [])
        emotional_tags = validated_data.pop('emotional_tags', [])

        user_state = UserState.objects.create(**validated_data)

        # Создаем связи через промежуточные таблицы
        UserStateTag.objects.bulk_create(
            [UserStateTag(user_state=user_state, tag=tag) for tag in tags]
        )

        UserEmotionalTag.objects.bulk_create(
            [UserEmotionalTag(user_state=user_state, emotional_tag=et) for et in emotional_tags]
        )

        return user_state

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Добавляем ID связанных объектов в вывод
        data['tags'] = [tag.id for tag in instance.tags]
        data['emotional_tags'] = [et.id for et in instance.emotional_tags]
        return data