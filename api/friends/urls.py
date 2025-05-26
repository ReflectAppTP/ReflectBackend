from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FriendshipViewSet, UserByUsernameView

router = DefaultRouter()
router.register(r'friendships', FriendshipViewSet, basename='friendship')

urlpatterns = [
    path('', include(router.urls)),
    path('by-username/<str:username>/', UserByUsernameView.as_view(), name='user-by-username'),
]