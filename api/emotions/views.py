from rest_framework import generics, permissions
from .models import UserState, EmotionalTag, Tag
from .serializers import UserStateSerializer, EmotionalTagSerializer, TagSerializer
from django.utils import timezone
from datetime import datetime

class UserStateView(generics.ListCreateAPIView):
    serializer_class = UserStateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = UserState.objects.filter(user=self.request.user)

        # Фильтрация по дате (YYYY-MM-DD)
        date = self.request.query_params.get('date', None)
        if date:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date=date_obj)
            except ValueError:
                pass

        # Фильтрация по временному промежутку
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                queryset = queryset.filter(created_at__range=[start, end])
            except ValueError:
                pass

        return queryset.order_by('-created_at')

class UserStateDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserStateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserState.objects.filter(user=self.request.user)

class EmotionalTagListView(generics.ListCreateAPIView):
    queryset = EmotionalTag.objects.all()
    serializer_class = EmotionalTagSerializer

class TagListView(generics.ListCreateAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer