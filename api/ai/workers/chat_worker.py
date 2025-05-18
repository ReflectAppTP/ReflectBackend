import os
import json
import asyncio
import aio_pika
import httpx
from aio_pika.abc import AbstractIncomingMessage

# Конфигурация
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
RABBITMQ_URL = f"amqp://{os.getenv('RABBITMQ_USER', 'admin')}:{os.getenv('RABBITMQ_PASS', 'password')}@{os.getenv('RABBITMQ_HOST', 'rabbitmq')}/"
DEEPSEEK_MODEL = "deepseek/deepseek-r1:free"


async def process_message(message: AbstractIncomingMessage):
    async with message.process():
        try:
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
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    },
                    json={
                        "model": DEEPSEEK_MODEL,
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
                    await message.nack(requeue=False)

        except Exception as e:
            print(f"Error processing message: {e}")
            await message.nack(requeue=False)


async def send_reply(reply_to: str, message_id: str, content: str):
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
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


async def main():
    while True:
        try:
            # Подключение к RabbitMQ
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            print("Connected to RabbitMQ")

            async with connection:
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=1)

                queue = await channel.declare_queue(
                    "chat_requests",
                    durable=True
                )

                print("Waiting for messages...")
                await queue.consume(process_message)

                # Бесконечное ожидание
                await asyncio.Future()

        except ConnectionError:
            print("RabbitMQ connection error, retrying in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())