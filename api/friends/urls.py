from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FriendshipViewSet, UsersByUsernamePrefixView, PendingFriendRequestsView

router = DefaultRouter()
router.register(r'friendships', FriendshipViewSet, basename='friendship')

urlpatterns = [
    path('', include(router.urls)),
    path('by-username/<str:username_prefix>/', UsersByUsernamePrefixView.as_view(), name='user-by-username'),
    path('requests/pending/', PendingFriendRequestsView.as_view()),

]