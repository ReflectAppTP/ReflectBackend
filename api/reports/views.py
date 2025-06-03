from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import StateReport, UserReport
from .serializers import StateReportSerializer, UserReportSerializer, BlockUserSerializer, AdminUsernameSerializer, AdminBlockStatusSerializer, AdminPrivilegesSerializer
from ..emotions.models import UserState

User = get_user_model()

class IsAdminUser(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_admin

class AdminReportViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=["get"])
    def users(self, request):
        users = User.objects.all()
        return Response([{"id": u.id, "username": u.username, "is_admin": u.is_admin, "email": u.email, "is_premium": u.is_premium, "is_blocked": u.is_blocked} for u in users])
    @action(detail=False, methods=["get"])
    def reports(self, request):
        state_reports = StateReport.objects.all()
        user_reports = UserReport.objects.all()
        return Response({
            "state_reports": StateReportSerializer(state_reports, many=True).data,
            "user_reports": UserReportSerializer(user_reports, many=True).data,
        })

    @action(detail=True, methods=["post"])
    def resolve_state(self, request, pk=None):
        report = StateReport.objects.get(pk=pk)
        accepted = request.data.get("accept", False)
        report.is_resolved = True
        report.is_accepted = accepted
        report.save()
        if accepted:
            report.state.delete()
        return Response({"resolved": True, "accepted": accepted})

    @action(detail=True, methods=['post'])
    def resolve_user(self, request, pk=None):
        try:
            report = UserReport.objects.get(pk=pk)
        except UserReport.DoesNotExist:
            return Response({"error": "Report not found"}, status=404)

        accept = request.data.get("accept", False)

        report.is_resolved = True
        report.is_accepted = accept
        report.save()

        if accept:
            reported = report.reported_user
            reported.is_blocked = True
            reported.save()

        return Response({
            "resolved": True,
            "accepted": accept,
            "user_blocked": accept
        })

    @action(detail=True, methods=["delete"])
    def delete_user(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
            user.delete()
            return Response({"deleted": True})
        except User.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

class UserReportViewSet(viewsets.ModelViewSet):
    queryset = UserReport.objects.all()
    serializer_class = UserReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)

class StateReportViewSet(viewsets.ModelViewSet):
    queryset = StateReport.objects.all()
    serializer_class = StateReportSerializer
    permission_classes = [permissions.IsAuthenticated]



    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)

class BlockUserView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        serializer = BlockUserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "user_id": user.id,
                "is_blocked": user.is_blocked
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminUserViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @action(detail=True, methods=['patch'], url_path='edit/username')
    def edit_username(self, request, pk=None):
        user = self.get_user(pk)
        if not user:
            return Response({"error": "User not found"}, status=404)
        serializer = AdminUsernameSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "login": serializer.data["login"]})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='edit/is_blocked')
    def edit_blocked(self, request, pk=None):
        user = self.get_user(pk)
        if not user:
            return Response({"error": "User not found"}, status=404)
        serializer = AdminBlockStatusSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "is_blocked": serializer.data["is_blocked"]})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='edit/is_admin')
    def edit_admin(self, request, pk=None):
        user = self.get_user(pk)
        if not user:
            return Response({"error": "User not found"}, status=404)
        serializer = AdminPrivilegesSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "is_admin": serializer.data["is_admin"]})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminUserStateDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, state_id):
        state = get_object_or_404(UserState, id=state_id)
        user = state.user

        return Response({
            "login": user.login,
            "email": user.email,
            "description": state.description
        })