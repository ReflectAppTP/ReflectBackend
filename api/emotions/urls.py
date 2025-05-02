from django.urls import path
from .views import UserStateListCreateView, UserStateRetrieveUpdateDestroyView

urlpatterns = [
    path('states/', UserStateListCreateView.as_view(), name='userstate-list'),
    path('states/<int:pk>/', UserStateRetrieveUpdateDestroyView.as_view(), name='userstate-detail'),
]