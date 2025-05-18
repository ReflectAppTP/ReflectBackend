import os
import requests
from django.conf import settings

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
class DeepSeekService:
    @staticmethod
    def get_response(messages):
        headers = {
            "Authorization": f"Bearer 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",
            "HTTP-Referer": settings.OPENROUTER_REFERER_URL,
            "X-Title": settings.OPENROUTER_APP_NAME,
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek/deepseek-r1:free",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }

        try:
            response = requests.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error calling DeepSeek API: {str(e)}")
            return "Sorry, I couldn't process your request at the moment."