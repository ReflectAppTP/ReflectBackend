from django.urls import path
from .views import DeepSeekRequestView, DeepSeekResultView, ChatSendView, ChatStatusView, reset_chat_session

urlpatterns = [
    path('analyze/', DeepSeekRequestView.as_view(), name='deepseek-request'),
    path('results/<str:correlation_id>/', DeepSeekResultView.as_view(), name='deepseek-result'),
    path('chat/send/', ChatSendView.as_view(), name='chat-send'),
    path('chat/status/<uuid:message_id>/', ChatStatusView.as_view(), name='chat-status'),
    path('chat/reset/', reset_chat_session, name='reset-chat')
]