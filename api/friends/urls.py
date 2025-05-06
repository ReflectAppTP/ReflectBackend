from django.urls import path
from . import views

urlpatterns = [
    path('', views.friends_list, name='friends-list'),
    path('<int:friend_id>/', views.friend_detail, name='friend-detail'),
    path('accept/', views.accept_friend, name='accept-friend'),
    path('<int:friend_id>/last_emotion/', views.friend_last_emotion, name='friend-last-emotion'),
    path('<int:friend_id>/statistic/', views.friend_statistic, name='friend-statistic'),
]