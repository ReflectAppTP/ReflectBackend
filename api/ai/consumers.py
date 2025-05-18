import os
import django
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reflect_backend_app.settings')
django.setup()

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
            message_id = message_data['message_id']
            user_id = message_data['user_id']
            content = message_data['content']

            print(f" [x] Received message {message_id} from user {user_id}")


            previous_messages = ChatMessage.objects.filter(
                user_id=user_id
            ).order_by('-created_at')[:5]


            messages = [
                {
                    "role": "user" if msg.status == 'pending' else "assistant",
                    "content": msg.content if msg.status == 'pending' else msg.response
                }
                for msg in reversed(previous_messages)
            ]
            messages.append({"role": "user", "content": content})


            deepseek = DeepSeekService()
            response = deepseek.get_response(messages)


            ChatMessage.objects.filter(message_id=message_id).update(
                response=response,
                status='processed'
            )

            print(f" [x] Processed message {message_id}")
        except Exception as e:
            print(f" [x] Error processing message: {str(e)}")
            ChatMessage.objects.filter(message_id=message_id).update(
                status='failed'
            )


if __name__ == "__main__":
    import django

    django.setup()
    consumer = ChatConsumer()
    consumer.start_consuming()