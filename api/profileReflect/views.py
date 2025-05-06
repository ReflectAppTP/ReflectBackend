from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

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