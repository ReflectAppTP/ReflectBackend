from django.utils import timezone
import threading
from concurrent.futures import ThreadPoolExecutor
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from api.emotions.models import UserState
from .deepseek_service import DeepSeekService
from .models import DeepSeekAnalysis, ChatMessage, ChatSession
import pika
import json


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




executor = ThreadPoolExecutor(max_workers=4)  # Пул потоков для обработки


class ChatSendView(APIView):
    def post(self, request):
        user = request.user
        content = request.data.get('content')

        if not content:
            return Response({"error": "Content is required"}, status=400)

        # Создаем сессию и сообщение
        session = ChatSession.objects.filter(
            user=user,
            is_active=True
        ).first() or ChatSession.objects.create(user=user)

        message = ChatMessage.objects.create(
            session=session,
            user=user,
            content=content,
            role='user',
            status='processing'  # Новый статус для отслеживания
        )

        # Получаем историю сообщений
        history = [
                      {"role": msg.role, "content": msg.content}
                      for msg in session.messages.all().order_by('-created_at')[:5]
                  ][::-1]

        # Синхронный вызов AI (с таймаутом)
        try:
            # Запускаем в отдельном потоке с таймаутом
            future = executor.submit(DeepSeekService.get_response, history)
            response_content = future.result(timeout=15)  # Таймаут 15 секунд

            # Сохраняем ответ
            message.response = response_content
            message.role = 'assistant'
            message.status = 'processed'
            message.save()

            return Response({
                "message_id": message.id,
                "response": response_content,
                "status": "processed"
            })

        except Exception as e:
            message.status = 'failed'
            message.save()
            return Response(
                {"error": str(e), "message_id": message.id},
                status=500
            )

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