from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import StateReport, UserReport
from .serializers import StateReportSerializer, UserReportSerializer

User = get_user_model()

class IsAdminUser(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_admin

class AdminReportViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=["get"])
    def users(self, request):
        users = User.objects.all()
        return Response([{"id": u.id, "username": u.username, "is_admin": u.is_admin} for u in users])

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

    @action(detail=True, methods=["post"])
    def resolve_user(self, request, pk=None):
        report = UserReport.objects.get(pk=pk)
        accepted = request.data.get("accept", False)
        report.is_resolved = True
        report.is_accepted = accepted
        report.save()
        if accepted:
            reported = report.reported_user
            reported.can_use_friends = False
            reported.save()
        return Response({"resolved": True, "accepted": accepted})

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