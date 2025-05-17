from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from api.emotions.models import UserState  # Используем существующую модель
from .models import DeepSeekAnalysis
import pika
import uuid
import json


class DeepSeekRequestView(APIView):
    """
    POST /api/ai/analyze/
    Анализирует эмоциональные состояния через DeepSeek
    """

    def post(self, request):
        # 1. Получаем последние 5 состояний пользователя
        states = UserState.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]

        if not states:
            return Response(
                {"error": "No emotional states found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Формируем запрос
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

        # 3. Сохраняем запрос в БД
        analysis = DeepSeekAnalysis.objects.create(
            user=request.user,
            correlation_id=str(uuid.uuid4()),
            input_data=analysis_data,
            status='processing'
        )

        # 4. Отправляем в RabbitMQ
        self._send_to_rabbitmq(analysis_data, analysis.correlation_id)

        return Response({
            "correlation_id": analysis.correlation_id,
            "status": "analysis_started"
        }, status=status.HTTP_202_ACCEPTED)

    def _send_to_rabbitmq(self, data, correlation_id):
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
                correlation_id=correlation_id,
                reply_to=settings.RABBITMQ['RESPONSE_QUEUE']
            ),
            body=json.dumps(data)
        )

        connection.close()


class DeepSeekResultView(APIView):
    """
    GET /api/ai/results/<correlation_id>/
    Проверяет статус анализа
    """

    def get(self, request, correlation_id):
        try:
            analysis = DeepSeekAnalysis.objects.get(
                correlation_id=correlation_id,
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