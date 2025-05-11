from django.urls import path
from .views import UserStateView, UserStateDetailView, EmotionalTagListView, TagListView, MoodStatisticsView, TagsStatisticsView, EmotionalTagsStatisticsView, MoodAverageStatisticsView

urlpatterns = [
    path('states/', UserStateView.as_view(), name='userstate-list'),
    path('states/<int:pk>/', UserStateDetailView.as_view(), name='userstate-detail'),
    path('emotional-tags/', EmotionalTagListView.as_view(), name='emotional-tags-list'),
    path('tags/', TagListView.as_view(), name='tags-list'),
    path('statistics/mood/', MoodStatisticsView.as_view(), name='mood-statistics'),
    path('statistics/tags/', TagsStatisticsView.as_view(), name='tags-statistics'),
    path('statistics/emotional-tags/', EmotionalTagsStatisticsView.as_view(), name='emotional-tags-statistics'),
    path('statistics/mood-average/', MoodAverageStatisticsView.as_view(), name='mood-average-statistics'),
]