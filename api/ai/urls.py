from django.urls import path
from .views import DeepSeekRequestView, DeepSeekResultView, ChatSendView, ChatStatusView, reset_chat_session, MessageStatusView

urlpatterns = [
    path('analyze/', DeepSeekRequestView.as_view(), name='deepseek-request'),
    path('results/<int:analysis_id>/', DeepSeekResultView.as_view()),
    path('chat/send/', ChatSendView.as_view(), name='chat-send'),
    path('status/<int:message_id>/', ChatStatusView.as_view()),
    path('chat/reset/', reset_chat_session, name='reset-chat'),
    path('chat/messages/<int:message_id>/', MessageStatusView.as_view(), name='message-status')
]