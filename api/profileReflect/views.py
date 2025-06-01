from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import VisibilityUpdateSerializer


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