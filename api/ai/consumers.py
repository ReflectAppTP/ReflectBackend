import os
import uuid
from datetime import timezone

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

    def process_message(ch, method, properties, body):
        try:
            data = json.loads(body)
            user_id = data['user_id']
            message_id = data['message_id']  # Получаем message_id из входящих данных
            content = data['content']

            # 1. Получаем или создаем активную сессию
            session = ChatSession.objects.filter(
                user_id=user_id,
                is_active=True
            ).first()

            if not session:
                session = ChatSession.objects.create(
                    user_id=user_id,
                    session_id=uuid.uuid4()
                )

            # 2. Создаем сообщение с ВСЕМИ обязательными полями
            message = ChatMessage.objects.create(
                session=session,
                user_id=user_id,
                message_id=message_id,  # Важно: передаем message_id
                content=content,
                role='user',
                status='pending'
            )

            # 3. Получаем историю сообщений (последние 10)
            history_messages = session.messages.all().order_by('-created_at')[:10]
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in reversed(history_messages)  # Правильный порядок
            ]

            # 4. Получаем ответ от AI
            response_content = DeepSeekService.get_response(history)

            # 5. Обновляем сообщение ответом
            message.response = response_content
            message.status = 'processed'
            message.save()

            print(f"Processed message {message_id}")

        except Exception as e:
            print(f"Error processing message {message_id}: {str(e)}")
            ChatMessage.objects.filter(message_id=message_id).update(
                status='failed'
            )


if __name__ == "__main__":
    import django

    django.setup()
    consumer = ChatConsumer()
    consumer.start_consuming()