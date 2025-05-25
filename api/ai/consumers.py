import os
from datetime import timezone
import logging
import django
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reflect_backend_app.settings')
django.setup()
from api.ai.models import ChatMessage, ChatSession

import json
import pika
from django.conf import settings

from deepseek_service import DeepSeekService

logger = logging.getLogger(__name__)

class ChatConsumer:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=settings.RABBITMQ['HOST'],
                credentials=pika.PlainCredentials(
                    settings.RABBITMQ['USER'],
                    settings.RABBITMQ['PASSWORD']
                )
            )
        )
        self.channel = self.connection.channel()


        self.channel.exchange_declare(exchange='chat_exchange', exchange_type='direct')
        self.channel.queue_declare(queue='chat_requests')
        self.channel.queue_bind(exchange='chat_exchange', queue='chat_requests', routing_key='chat_requests')

    def start_consuming(self):
        self.channel.basic_consume(
            queue='chat_requests',
            on_message_callback=self.process_message,
            auto_ack=True
        )
        print(" [*] Waiting for messages. To exit press CTRL+C")
        self.channel.start_consuming()

    def process_message(channel, method, properties, body, *args):
        try:
            data = json.loads(body)
            user_id = data['user_id']
            content = data['content']
            message_id = data['message_id']
            session_id = data['session_id']

            # Получаем или создаем сессию
            session = ChatSession.objects.filter(
                user_id=user_id,
                is_active=True
            ).first()

            if not session:
                session = ChatSession.objects.create(
                    user_id=user_id,
                    created_at=timezone.now()
                )

            # Создаем сообщение
            message = ChatMessage.objects.create(
                session=session,
                user_id=user_id,
                content=content,
                role='user',
                status='pending'
            )

            # Получаем историю сообщений
            history_messages = session.messages.all().order_by('-created_at')[:10]
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in reversed(history_messages)
            ]

            # Получаем ответ от AI
            response = DeepSeekService.get_response(history)

            # Обновляем сообщение
            message.response = response
            message.status = 'processed'
            message.role = 'assistant'
            message.save()

            # Подтверждаем обработку сообщения
            channel.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            if 'message' in locals():
                message.status = 'failed'
                message.save()


if __name__ == "__main__":
    import django

    django.setup()
    consumer = ChatConsumer()
    consumer.start_consuming()