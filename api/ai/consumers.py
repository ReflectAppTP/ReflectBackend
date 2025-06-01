import os
import json
import pika
import django
import sys

from datetime import timezone
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from api.ai.models import ChatMessage, ChatSession
from django.conf import settings

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reflect_backend_app.settings')
django.setup()


from api.ai.deepseek_service import DeepSeekService


class ChatConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        try:
            # Параметры подключения с таймаутами
            credentials = pika.PlainCredentials(
                settings.RABBITMQ['USER'],
                settings.RABBITMQ['PASSWORD']
            )
            parameters = pika.ConnectionParameters(
                host=settings.RABBITMQ['HOST'],
                credentials=credentials,
                heartbeat=600,  # 10 минут
                blocked_connection_timeout=300,  # 5 минут
                connection_attempts=3,  # Количество попыток
                retry_delay=5  # Задержка между попытками
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Объявляем exchange и очередь
            self.channel.exchange_declare(
                exchange='chat_exchange',
                exchange_type='direct',
                durable=True
            )
            self.channel.queue_declare(
                queue='chat_requests',
                durable=True
            )
            self.channel.queue_bind(
                exchange='chat_exchange',
                queue='chat_requests',
                routing_key='chat_requests'
            )

            print(" [*] Successfully connected to RabbitMQ")

        except pika.exceptions.AMQPError as e:
            print(f" [x] Connection failed: {str(e)}")
            raise

    def process_message(self, ch, method, properties, body):
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
            ).first() or ChatSession.objects.create(
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
            history = [
                          {"role": msg.role, "content": msg.content}
                          for msg in session.messages.all().order_by('-created_at')[:10]
                      ][::-1]

            # Получаем ответ от AI
            response = DeepSeekService.get_response(history)

            # Обновляем сообщение
            message.response = response
            message.status = 'processed'
            message.role = 'assistant'
            message.save()

            # Подтверждаем обработку
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print(f" [x] Processed message {message_id}")

        except Exception as e:
            print(f" [x] Error processing message: {str(e)}")
            if 'message' in locals():
                message.status = 'failed'
                message.save()
            # Не подтверждаем сообщение при ошибке

    def start_consuming(self):
        self.channel.basic_consume(
            queue='chat_requests',
            on_message_callback=self.process_message,
            auto_ack=False
        )
        print(" [*] Waiting for messages. To exit press CTRL+C")
        self.channel.start_consuming()

    def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()

class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        from django.contrib.auth.models import AnonymousUser

        user = self.scope["user"]
        if user is None or isinstance(user, AnonymousUser):
            await self.close()
        else:
            self.group_name = f"user_{user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        user = self.scope["user"]
        if user and hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        await self.send_json({
            "type": "notification",
            "message": event["message"]
        })

if __name__ == '__main__':
    consumer = None
    try:
        consumer = ChatConsumer()
        consumer.start_consuming()
    except KeyboardInterrupt:
        print(" [x] Stopping consumer...")
    except Exception as e:
        print(f" [x] Error: {str(e)}")
    finally:
        if consumer:
            consumer.close()