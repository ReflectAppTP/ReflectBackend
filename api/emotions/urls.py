from django.urls import path
from .views import *

urlpatterns = [
    path('states/', UserStateListView.as_view(), name='state-list'),
    path('states/create/', UserStateCreateView.as_view(), name='state-create'),
    path('tags/', TagListView.as_view(), name='tag-list'),
    path('emotional-tags/', EmotionalTagListView.as_view(), name='emotional-tag-list'),
]