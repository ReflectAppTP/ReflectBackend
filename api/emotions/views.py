from rest_framework import generics, permissions
from .models import UserState, EmotionalTag, Tag
from .serializers import UserStateSerializer, EmotionalTagSerializer, TagSerializer

class UserStateView(generics.ListCreateAPIView):
    serializer_class = UserStateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserState.objects.filter(user=self.request.user)\
            .prefetch_related('tags', 'emotional_tags')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserStateDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserStateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserState.objects.filter(user=self.request.user)

class EmotionalTagListView(generics.ListAPIView):
    queryset = EmotionalTag.objects.all()
    serializer_class = EmotionalTagSerializer

class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer