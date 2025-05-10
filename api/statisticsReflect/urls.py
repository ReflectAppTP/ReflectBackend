from django.urls import path
from .views import MoodStatisticsView

urlpatterns = [
    path('mood/', MoodStatisticsView.as_view(), name='mood-statistics'),
]