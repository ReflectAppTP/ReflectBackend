import pika
import json
from transformers import AutoModelForCausalLM, AutoTokenizer

# Загрузка модели DeepSeek R1
model_name = "deepseek-ai/deepseek-r1"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)


def process_message(ch, method, properties, body):
    try:
        data = json.loads(body)
        message_id = data['message_id']
        user_id = data['user_id']
        content = data['content']

        # Генерация ответа
        inputs = tokenizer(content, return_tensors="pt")
        outputs = model.generate(**inputs, max_length=200)
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Отправка ответа в RabbitMQ
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=os.getenv('RABBITMQ_HOST'),
                credentials=pika.PlainCredentials(
                    os.getenv('RABBITMQ_USER'),
                    os.getenv('RABBITMQ_PASS')
                )
            )
        )
        channel = connection.channel()

        channel.basic_publish(
            exchange='chat_exchange',
            routing_key=f'chat_responses_{user_id}',
            body=json.dumps({
                'message_id': message_id,
                'response': response
            })
        )

        connection.close()
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"Error: {e}")


def start_worker():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.getenv('RABBITMQ_HOST'),
            credentials=pika.PlainCredentials(
                os.getenv('RABBITMQ_USER'),
                os.getenv('RABBITMQ_PASS')
            )
        )
    )
    channel = connection.channel()

    channel.queue_declare(queue='chat_requests', durable=True)
    channel.basic_consume(
        queue='chat_requests',
        on_message_callback=process_message,
        auto_ack=False
    )

    print(" [*] DeepSeek R1 Worker started. Waiting for messages...")
    channel.start_consuming()


if __name__ == '__main__':
    import os

    start_worker()