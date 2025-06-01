from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .models import Friendship
from django.contrib.auth import get_user_model
from .serializers import (
    FriendshipSerializer,
    CreateFriendshipSerializer,
    UpdateFriendshipSerializer, UserSerializer
)
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import Q
from django.shortcuts import get_object_or_404



class FriendshipViewSet(viewsets.ModelViewSet):
    queryset = Friendship.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateFriendshipSerializer
        elif self.action in ['partial_update', 'update']:
            return UpdateFriendshipSerializer
        return FriendshipSerializer

    def get_queryset(self):
        user = self.request.user
        return Friendship.objects.filter(
            Q(from_user=user) | Q(to_user=user))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.user.id == serializer.validated_data['to_user_id']:
            return Response(
                {"error": "You cannot send friend request to yourself"},
                status=status.HTTP_400_BAD_REQUEST
            )

        friendship, created = Friendship.objects.get_or_create(
            from_user=request.user,
            to_user_id=serializer.validated_data['to_user_id'],
            defaults={'status': Friendship.PENDING}
        )
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{serializer.validated_data['to_user_id']}",
            {
                "type": "send_notification",
                "message": f"New friend request {request.user.username}"
            }
        )
        if not created:
            return Response(
                {"error": "Friend request already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            FriendshipSerializer(friendship).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        friendship = self.get_object()
        if friendship.to_user != request.user:
            return Response(
                {"error": "You can't accept this request"},
                status=status.HTTP_403_FORBIDDEN
            )

        friendship.status = Friendship.ACCEPTED
        friendship.save()
        return Response(
            FriendshipSerializer(friendship).data
        )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        friendship = self.get_object()
        if friendship.to_user != request.user:
            return Response(
                {"error": "You can't reject this request"},
                status=status.HTTP_403_FORBIDDEN
            )

        friendship.status = Friendship.REJECTED
        friendship.save()
        return Response(
            FriendshipSerializer(friendship).data
        )

    @action(detail=False, methods=['get'])
    def listf(self, request):
        friendships = Friendship.objects.filter(
            Q(from_user=request.user) | Q(to_user=request.user),
            status=Friendship.ACCEPTED
        )

        friends = []
        for f in friendships:
            friend = f.from_user if f.from_user != request.user else f.to_user
            friends.append(friend)

        serializer = UserSerializer(friends, many=True)
        return Response(serializer.data)

User = get_user_model()

class UsersByUsernamePrefixView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, username_prefix):
        users = User.objects.filter(username__istartswith=username_prefix).exclude(id=request.user.id)

        response_data = []
        for user in users:
            is_friend = Friendship.objects.filter(
                (Q(from_user=request.user) & Q(to_user=user)) |
                (Q(from_user=user) & Q(to_user=request.user)),
                status=Friendship.ACCEPTED
            ).exists()

            response_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "date_joined": user.created_at,
                "is_friend": is_friend,
                "is_premium": user.is_premium
            })

        return Response(response_data)