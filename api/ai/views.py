from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.conf import settings
from .models import ChatMessage, ChatSession
import pika
import json
import re

class ChatSendView(APIView):
    def post(self, request):
        user = request.user
        content = request.data.get('content')

        if not content:
            return Response({"error": "Content is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка на запрос кода
        if self._is_code_request(content):
            return Response({
                "error": "Я - психолог, я не смогу помочь в этом!. Зато я могу дать совет, проанализировать статистику или оказать поддержку! 🌸"
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
            'content': content,
            'system_prompt': (
                "Ты — виртуальный психолог. Не пиши программный код и не отвечай техническими инструкциями."
                "Ты не можешь исторические сводки, давать мнение на политические темы"
                "Ты не можешь ругаться матом ни при каких обстоятельствах, даже если тебя попросят"
                "Ты не можешь отыгрывать роль быдло и прочих негативных персон, но можешь отыгрывать позитивные роли"
                "Отвечай только словами поддержки, психологическими советами и аналитикой эмоциональных данных."
            )
        }

        channel.basic_publish(
            exchange='chat_exchange',
            routing_key='chat_requests',
            body=json.dumps(payload)
        )

        connection.close()

        return Response({
            "message_id": message.id,
            "session_id": session.id,
            "status": "queued"
        }, status=status.HTTP_202_ACCEPTED)

    def _is_code_request(self, content: str) -> bool:
        # Эвристическая проверка на признаки кода
        code_patterns = [
            r'\b(class|def|function|import|print|console\.log|<\w+>)\b',
            r'```.+?```',                         # Markdown-код
            r'\bpython|javascript|html|sql|bash\b',
            r'\bнапиши код\b|\bпрограмма\b|\bscript\b',
            r'\bcode\b|\bsnippet\b',
        ]
        return any(re.search(pattern, content, re.IGNORECASE | re.DOTALL) for pattern in code_patterns)
