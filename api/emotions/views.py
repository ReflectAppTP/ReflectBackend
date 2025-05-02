from rest_framework import generics, permissions
from .models import UserState
from .serializers import UserStateSerializer

class UserStateView(generics.ListCreateAPIView):
    serializer_class = UserStateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserState.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserStateDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserStateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserState.objects.filter(user=self.request.user)