import pika
import json
import django
import os
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

from .models import DeepSeekAnalysis


def start_consumer():
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

    def callback(ch, method, properties, body):
        try:
            data = json.loads(body)
            correlation_id = properties.correlation_id

            # 1. Получаем анализ от DeepSeek (заглушка)
            result = {
                "analysis": "positive",
                "recommendations": ["get more sleep", "practice mindfulness"]
            }

            # 2. Обновляем запись в БД
            analysis = DeepSeekAnalysis.objects.get(
                correlation_id=correlation_id
            )
            analysis.output_result = result
            analysis.status = 'completed'
            analysis.save()

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"Error processing message: {e}")
            analysis.status = 'failed'
            analysis.save()

    channel.basic_consume(
        queue=settings.RABBITMQ['RESPONSE_QUEUE'],
        on_message_callback=callback,
        auto_ack=False
    )

    print(" [*] Waiting for DeepSeek results. To exit press CTRL+C")
    channel.start_consuming()


if __name__ == '__main__':
    start_consumer()