import re

from django.utils import timezone
from rest_framework.exceptions import NotFound
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from api.emotions.models import UserState, UserEmotionalTag
from .models import DeepSeekAnalysis, ChatMessage, ChatSession
import pika
import json
from django.db.models import Avg, Count
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta


@api_view(['POST'])
def reset_chat_session(request):
    ChatSession.objects.filter(
        user=request.user,
        is_active=True
    ).update(is_active=False)

    new_session = ChatSession.objects.create(user=request.user)

    return Response({
        "session_id": new_session.id,  # Используем стандартный id
        "message": "Chat session reset"
    })

class DeepSeekRequestView(APIView):
    def post(self, request):
        states = UserState.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]

        if not states:
            return Response(
                {"error": "No emotional states found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        analysis_data = {
            "user_id": request.user.id,
            "states": [
                {
                    "description": state.description,
                    "value": state.value,
                    "tags": [tag.name for tag in state.tags.all()],
                    "emotional_tags": [etag.name for etag in state.emotional_tags.all()]
                }
                for state in states
            ]
        }

        analysis = DeepSeekAnalysis.objects.create(
            user=request.user,
            input_data=analysis_data,
            status='processing'
        )

        self._send_to_rabbitmq(analysis_data, analysis.id)  # Используем стандартный id

        return Response({
            "analysis_id": analysis.id,  # Возвращаем стандартный id
            "status": "analysis_started"
        }, status=status.HTTP_202_ACCEPTED)

    def _send_to_rabbitmq(self, data, analysis_id):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=settings.RABBITMQ['HOST'],
                credentials=pika.PlainCredentials(
                    settings.RABBITMQ['USER'],
                    settings.RABBITMQ['PASSWORD']
                )
            )
        )
        channel = connection.channel()

        channel.basic_publish(
            exchange=settings.RABBITMQ['EXCHANGE'],
            routing_key=settings.RABBITMQ['REQUEST_QUEUE'],
            properties=pika.BasicProperties(
                correlation_id=str(analysis_id),  # Преобразуем в строку для RabbitMQ
                reply_to=settings.RABBITMQ['RESPONSE_QUEUE']
            ),
            body=json.dumps(data)
        )

        connection.close()

class DeepSeekResultView(APIView):
    def get(self, request, analysis_id):  # Принимаем стандартный id
        try:
            analysis = DeepSeekAnalysis.objects.get(
                id=analysis_id,  # Ищем по стандартному id
                user=request.user
            )
            return Response({
                "status": analysis.status,
                "result": analysis.output_result if analysis.status == 'completed' else None
            })
        except DeepSeekAnalysis.DoesNotExist:
            return Response(
                {"error": "Analysis not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class ChatSendView(APIView):
    def _get_weekly_stats(self, user):
        today = datetime.now().date()
        start_date = today - timedelta(days=6)

        # Среднее настроение по дням
        mood_data = UserState.objects.filter(
            user=user,
            created_at__date__range=(start_date, today)
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            avg_mood=Avg('value')
        ).order_by('date')

        mood_stats = [{
            "date": item['date'].strftime('%Y-%m-%d'),
            "average_mood": round(item['avg_mood'], 2)
        } for item in mood_data]

        # Эмоциональные теги за период
        tag_queryset = UserEmotionalTag.objects.filter(
            user_state__user=user,
            user_state__created_at__date__range=(start_date, today)
        )

        top_tags = tag_queryset.values(
            'emotional_tag_id', 'emotional_tag__name', 'emotional_tag__emoji'
        ).annotate(
            freq=Count('user_state', distinct=True)
        ).order_by('-freq')[:5]

        tag_stats = [{
            "id": item['emotional_tag_id'],
            "name": item['emotional_tag__name'],
            "emoji": item['emotional_tag__emoji'],
            "freq": item['freq']
        } for item in top_tags]

        return {
            "weekly_mood": mood_stats,
            "top_emotional_tags": tag_stats
        }

    def build_deepseek_messages(content, stats):
        system_prompt = (
            "Ты — доброжелательный виртуальный психолог.\n"
            "Ты получаешь сообщение пользователя в поле 'content', "
            "а также статистику его эмоционального состояния за последние 7 дней.\n\n"
            "Поле 'stats' включает:\n"
            "- 'weekly_mood': список дат и среднее настроение (от 1 до 5),\n"
            "- 'top_emotional_tags': наиболее частые эмоции (с эмодзи).\n\n"
            "Твоя задача — использовать эти данные, чтобы дать психологический совет, поддержку или анализ.\n"
            "Никогда не пиши программный код, команды, скрипты или технические инструкции. "
            "Отвечай просто, по-человечески, как тёплый и внимательный психолог."
        )

        user_message = (
                f"Пользователь написал: {content}\n\n"
                f"Данные за последнюю неделю:\n\n"
                f"📊 Настроение по дням:\n" +
                "\n".join([f"{item['date']}: {item['average_mood']}" for item in stats.get("weekly_mood", [])]) +
                "\n\n🧠 Частые эмоциональные теги:\n" +
                "\n".join([f"{tag['emoji']} {tag['name']} — {tag['freq']} раз(а)" for tag in
                           stats.get("top_emotional_tags", [])])
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

    def post(self, request):
        user = request.user
        content = request.data.get('content')

        if not content:
            return Response({"error": "Content is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка на запрос кода
        if self._is_code_request(content):
            return Response({
                "error": "Я — психолог, я не смогу помочь в этом! Зато могу дать совет, проанализировать статистику или оказать поддержку! 🌸"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Получаем или создаем активную сессию
        session, _ = ChatSession.objects.get_or_create(
            user=user,
            is_active=True,
            defaults={'created_at': timezone.now()}
        )

        # Создаем сообщение
        message = ChatMessage.objects.create(
            session=session,
            user=user,
            content=content,
            status='pending'
        )

        # Получаем статистику
        stats = self._get_weekly_stats(user)

        # Формируем messages для DeepSeek
        messages = self.build_deepseek_messages(content, stats)

        # Отправка в RabbitMQ
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=settings.RABBITMQ['HOST'],
                credentials=pika.PlainCredentials(
                    settings.RABBITMQ['USER'],
                    settings.RABBITMQ['PASSWORD']
                )
            )
        )
        channel = connection.channel()

        payload = {
            'message_id': message.id,
            'session_id': session.id,
            'user_id': user.id,
            'messages': messages
        }

        channel.basic_publish(
            exchange='chat_exchange',
            routing_key='chat_requests',
            body=json.dumps(payload, ensure_ascii=False)
        )

        connection.close()

        return Response({
            "message_id": message.id,
            "session_id": session.id,
            "status": "queued"
        }, status=status.HTTP_202_ACCEPTED)


class MessageStatusView(APIView):
    """
    GET /api/chat/messages/<int:message_id>/
    Возвращает статус и ответ сообщения
    """

    def get(self, request, message_id):
        try:
            message = ChatMessage.objects.get(
                id=message_id,
                user=request.user  # Проверяем, что сообщение принадлежит пользователю
            )

            return Response({
                "status": message.status,
                "response": message.response if message.status == 'processed' else None,
                "created_at": message.created_at
            })

        except ChatMessage.DoesNotExist:
            raise NotFound(detail="Message not found")

class ChatStatusView(APIView):
    def get(self, request, message_id):  # Принимаем стандартный id
        try:
            message = ChatMessage.objects.get(
                id=message_id,  # Ищем по стандартному id
                user=request.user
            )
            return Response({
                "status": message.status,
                "response": message.response if message.status == 'processed' else None
            })
        except ChatMessage.DoesNotExist:
            return Response({"error": "Message not found"}, status=404)


