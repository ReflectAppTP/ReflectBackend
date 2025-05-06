from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(['GET'])
def friends_list(request):
    return Response([
        {"id": 1, "name": "Друг 1", "status": "active"},
        {"id": 2, "name": "Друг 2", "status": "pending"}
    ], status=status.HTTP_200_OK)

@api_view(['GET', 'DELETE'])
def friend_detail(request, friend_id):
    if request.method == 'GET':
        return Response({
            "id": friend_id,
            "name": f"Друг {friend_id}",
            "last_emotion": "happy"
        })
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
def accept_friend(request):
    return Response({"status": "ok"}, status=status.HTTP_200_OK)

@api_view(['GET'])
def friend_last_emotion(request, friend_id):
    return Response({
        "friend_id": friend_id,
        "emotion": "happy",
        "value": 8,
        "timestamp": "2023-05-20T14:30:00Z"
    })

@api_view(['GET'])
def friend_statistic(request, friend_id):
    return Response({
        "friend_id": friend_id,
        "stats": {
            "weekly_avg": 6.5,
            "top_tags": ["work", "sport"]
        }
    })