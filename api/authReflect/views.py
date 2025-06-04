from django.utils.crypto import get_random_string
from rest_framework import generics, status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .serializers import RegisterSerializer, UserSerializer, LoginSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import UserSerializer
from ..emotions.models import UserState
from ..friends.models import Friendship


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": UserSerializer(user).data,
            "message": "User created successfully",
        }, status=status.HTTP_201_CREATED)

class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]  # Требует валидный access-токен

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class GuestLoginView(APIView):
    def post(self, request):
        username = f"guest_{get_random_string(length=8)}"
        email = f"{username}@guest.local"

        guest_user = User.objects.create(
            username=username,
            email=email,
            is_guest=True,
        )

        refresh = RefreshToken.for_user(guest_user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "username": username,
            "is_guest": True
        })

class RegisterFromGuestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        guest_user = request.user

        if not getattr(guest_user, 'is_guest', False):
            return Response({"error": "Нельзя выполнить перенос — пользователь не является гостем"}, status=400)

        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if not (username and email and password):
            return Response({"error": "Неполные данные"}, status=400)

        new_user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_guest=False
        )

        UserState.objects.filter(user=guest_user).update(user=new_user)
        guest_user.delete()

        return Response({"success": True, "username": new_user.username})