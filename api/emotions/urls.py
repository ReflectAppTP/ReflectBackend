from django.urls import path
from .views import UserStateView, UserStateDetailView, EmotionalTagListView, TagListView

urlpatterns = [
    path('states/', UserStateView.as_view(), name='userstate-list'),
    path('states/<int:pk>/', UserStateDetailView.as_view(), name='userstate-detail'),
    path('emotional-tags/', EmotionalTagListView.as_view(), name='emotional-tags-list'),
    path('tags/', TagListView.as_view(), name='tags-list'),
]