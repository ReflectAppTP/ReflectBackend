from django.urls import path
from .views import DeepSeekRequestView, DeepSeekResultView

urlpatterns = [
    path('analyze/', DeepSeekRequestView.as_view(), name='deepseek-request'),
    path('results/<str:correlation_id>/', DeepSeekResultView.as_view(), name='deepseek-result'),
]