import os
import requests
from django.conf import settings


class DeepSeekService:
    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

    @staticmethod
    def get_response(messages):
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
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
                self.OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error calling DeepSeek API: {str(e)}")
            return "Sorry, I couldn't process your request at the moment."