from django.urls import path
from . import views

urlpatterns = [
    path('trends/', views.ai_trends, name='ai-trends'),
    path('advice/', views.ai_advice, name='ai-advice'),
]