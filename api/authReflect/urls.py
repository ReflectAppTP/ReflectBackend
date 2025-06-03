from django.urls import path
from .views import RegisterView, UserProfileView, GuestLoginView, register_user_from_guest
from rest_framework_simplejwt.views import TokenObtainPairView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('guest-login/', GuestLoginView.as_view()),
    path("register-from-guest/", register_user_from_guest),
]