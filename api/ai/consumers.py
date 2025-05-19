import os
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

    def process_message(self, ch, method, properties, body):
        try:

            message_data = json.loads(body)
            user_id = message_data.get('user_id')
            message_id = message_data.get('message_id')
            content = message_data.get('content')


            if not all([user_id, message_id, content]):
                print(" [x] Invalid message format")
                return

            print(f" [x] Processing message {message_id} from user {user_id}")


            session, created = ChatSession.objects.get_or_create(
                user_id=user_id,
                is_active=True,
                defaults={'user_id': user_id}
            )


            if session.messages.count() >= 20:
                session.is_active = False
                session.save()
                session = ChatSession.objects.create(user_id=user_id)


            ChatMessage.objects.create(
                session=session,
                message_id=message_id,
                content=content,
                role='user',
                status='processing'
            )


            history_messages = session.messages.all().order_by('-created_at')[:10]
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in reversed(history_messages)
            ]


            response_content = DeepSeekService.get_response(history)


            ChatMessage.objects.filter(message_id=message_id).update(
                response=response_content,
                status='processed',
                role='assistant'
            )

            print(f" [x] Completed processing message {message_id}")

        except Exception as e:
            print(f" [x] Error processing message: {str(e)}")
            if 'message_id' in locals():
                ChatMessage.objects.filter(message_id=message_id).update(
                    status='failed'
                )


if __name__ == "__main__":
    import django

    django.setup()
    consumer = ChatConsumer()
    consumer.start_consuming()