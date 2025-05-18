import os
import json
import asyncio
import aio_pika
import httpx
from django.conf import settings
from aio_pika.abc import AbstractIncomingMessage
import reflect_backend_app

async def process_message(message: AbstractIncomingMessage):
    try:
        async with message.process(requeue=False):
            data = json.loads(message.body.decode())
            message_id = data["message_id"]
            prompt = data["content"]
            reply_to = message.reply_to

            print(f"Processing message {message_id}")

            # Запрос к OpenRouter
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                        "HTTP-Referer": "https://your-app.com",
                        "X-Title": "Reflect"
                    },
                    json={
                        "model": "deepseek/deepseek-r1:free",
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    reply_content = result["choices"][0]["message"]["content"]

                    # Отправка ответа
                    await send_reply(reply_to, message_id, reply_content)
                    print(f"Processed message {message_id}")
                else:
                    print(f"OpenRouter error: {response.text}")

    except Exception as e:
        print(f"Error processing message: {e}")


async def send_reply(reply_to: str, message_id: str, content: str):
    connection = await get_rabbitmq_connection()
    async with connection:
        channel = await connection.channel()

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps({
                    "message_id": message_id,
                    "content": content
                }).encode(),
                correlation_id=message_id
            ),
            routing_key=reply_to
        )


async def get_rabbitmq_connection():
    """Создает подключение к RabbitMQ с настройками из Django"""
    return await aio_pika.connect_robust(
        host=settings.RABBITMQ['HOST'],
        port=settings.RABBITMQ['PORT'],
        login=settings.RABBITMQ['USER'],
        password=settings.RABBITMQ['PASSWORD'],
        virtualhost="/",  # или settings.RABBITMQ.get('VHOST', '/')
        timeout=10  # сек
    )


async def main():
    while True:
        try:
            # Подключение с настройками из Django
            connection = await get_rabbitmq_connection()
            print("Connected to RabbitMQ")

            async with connection:
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=1)

                queue = await channel.declare_queue(
                    settings.RABBITMQ['REQUEST_QUEUE'],
                    durable=True
                )

                print(f"Waiting for messages in {settings.RABBITMQ['REQUEST_QUEUE']}...")
                await queue.consume(process_message)

                await asyncio.Future()

        except ConnectionError:
            print("RabbitMQ connection error, retrying in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    # Инициализация Django
    import os
    import django

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reflect_backend_app.settings')
    django.setup()

    asyncio.run(main())