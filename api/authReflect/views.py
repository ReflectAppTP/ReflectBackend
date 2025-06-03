from rest_framework import generics, status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .serializers import RegisterSerializer, UserSerializer, LoginSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer
from ..emotions.models import UserState
from ..friends.models import Friendship


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

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
        guest_user, created = User.objects.get_or_create(
            username='guest',
            defaults={'is_guest': True, 'email': 'guest@reflect.app'}
        )
        # Важно: не ставим пароль — нельзя войти обычным способом
        refresh = RefreshToken.for_user(guest_user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        })

def register_user_from_guest(request):
    guest_user = request.user

    if not getattr(guest_user, 'is_guest', False):
        return Response({"error": "Нельзя выполнить перенос — пользователь не является гостем"}, status=400)

    # Получаем данные из формы
    username = request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")

    if not (username and email and password):
        return Response({"error": "Неполные данные"}, status=400)

    # Создаём обычного пользователя
    new_user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        is_guest=False
    )

    # Переносим все UserState
    UserState.objects.filter(user=guest_user).update(user=new_user)

    # Удаляем гостя
    guest_user.delete()

    return Response({"success": True, "username": new_user.username})