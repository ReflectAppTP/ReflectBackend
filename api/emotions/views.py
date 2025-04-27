from rest_framework import generics, permissions
from .models import UserState, Tag, EmotionalTag
from .serializers import UserStateSerializer, CreateUserStateSerializer, TagSerializer, EmotionalTagSerializer

class UserStateCreateView(generics.CreateAPIView):
    queryset = UserState.objects.all()
    serializer_class = CreateUserStateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserStateListView(generics.ListAPIView):
    serializer_class = UserStateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserState.objects.filter(user=self.request.user)

class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]

class EmotionalTagListView(generics.ListAPIView):
    queryset = EmotionalTag.objects.all()
    serializer_class = EmotionalTagSerializer
    permission_classes = [permissions.IsAuthenticated]