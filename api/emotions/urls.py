from django.urls import path
from .views import UserStateView, UserStateDetailView

urlpatterns = [
    path('states/', UserStateView.as_view(), name='userstate-list'),
    path('states/<int:pk>/', UserStateDetailView.as_view(), name='userstate-detail'),
]