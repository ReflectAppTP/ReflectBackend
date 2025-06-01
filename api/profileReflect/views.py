from django.contrib.auth import get_user_model
from django.db.models import Q, Avg
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import VisibilityUpdateSerializer
from api.friends.models import Friendship
from datetime import datetime, timedelta

from ..emotions.models import UserState
from ..emotions.serializers import TagSerializer, EmotionalTagSerializer

User = get_user_model()

@api_view(['GET', 'PATCH', 'DELETE'])
def profile(request, user_id):
    if request.method == 'GET':
        return Response({
            "id": user_id,
            "username": "user_" + str(user_id),
            "premium": False
        })
    elif request.method == 'PATCH':
        return Response({"status": "updated"}, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_204_NO_CONTENT)

class UpdateVisibilityView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = VisibilityUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "visibility": serializer.data["visibility"]})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetailWithStateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_friendship_status(self, request_user, target_user):
        # Заблокирован
        if target_user.is_blocked:
            return 'blocked'
        # Дружба
        is_friend = Friendship.objects.filter(
            ((Q(from_user=request_user) & Q(to_user=target_user)) |
             (Q(from_user=target_user) & Q(to_user=request_user))),
            status='accepted'
        ).exists()
        return 'friend' if is_friend else 'not_friend'

    def get_week_stats(self, user):
        today = datetime.now().date()
        start_date = today - timedelta(days=6)

        stats = UserState.objects.filter(
            user=user,
            created_at__date__range=(start_date, today)
        ).annotate(date=TruncDate('created_at')).values('date').annotate(
            avg_mood=Avg('value')
        ).order_by('date')

        return [{
            "date": item['date'].strftime('%Y-%m-%d'),
            "average_mood": round(item['avg_mood'], 2)
        } for item in stats]

    def get_last_state(self, user):
        today = datetime.now().date()
        state = UserState.objects.filter(
            user=user,
            created_at__date=today
        ).order_by('-created_at').first()

        if not state:
            return None

        return {
            "id": state.id,
            "description": state.description,
            "value": state.value,
            "created_at": state.created_at.strftime('%Y-%m-%d %H:%M'),
            "tags": TagSerializer(state.tags.all(), many=True).data,
            "emotional_tags": EmotionalTagSerializer(state.emotional_tags.all(), many=True).data
        }

    def get(self, request, user_id):
        target_user = get_object_or_404(User, id=user_id)
        friendship_status = self.get_friendship_status(request.user, target_user)

        response = {
            "id": target_user.id,
            "username": target_user.username,
            "friendship_status": friendship_status,
        }

        # Разрешена ли видимость
        if target_user.visibility == 'all':
            response["last_state"] = self.get_last_state(target_user)
            response["week"] = self.get_week_stats(target_user)

        elif target_user.visibility == 'friends' and friendship_status == 'friend':
            response["last_state"] = self.get_last_state(target_user)
            response["week"] = self.get_week_stats(target_user)

        # visibility == 'self' → ничего не добавляем

        return Response(response)