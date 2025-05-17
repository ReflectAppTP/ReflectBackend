import httpx
import json
import os
from pika.exceptions import AMQPConnectionError

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DEEPSEEK_MODEL = "deepseek-ai/deepseek-r1"  # Идентификатор модели на OpenRouter


async def process_message(ch, method, properties, body):
    try:
        data = json.loads(body)
        message_id = data["message_id"]
        prompt = data["content"]

        # Запрос к OpenRouter
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "YOUR_APP_URL",  # Замените на ваш URL
                    "X-Title": "Reflect"  # Название вашего приложения
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

                # Отправка ответа в RabbitMQ
                await send_reply(
                    message_id=message_id,
                    content=reply_content
                )

                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                print(f"OpenRouter error: {response.text}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    except Exception as e:
        print(f"Error: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


async def send_reply(message_id: str, content: str):
    # Реализация отправки ответа в RabbitMQ
    pass