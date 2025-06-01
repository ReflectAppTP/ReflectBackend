from django.urls import path, include
from .views import AdminReportViewSet
from rest_framework.routers import DefaultRouter
from .views import UserReportViewSet, StateReportViewSet

admin_reports = AdminReportViewSet.as_view({
    "get": "reports",
    "post": "resolve_state",
})

router = DefaultRouter()
router.register(r'user', UserReportViewSet, basename='user-report')
router.register(r'state', StateReportViewSet, basename='state-report')

urlpatterns = [
    path("admin/users/", AdminReportViewSet.as_view({"get": "users"})),
    path("admin/reports/", AdminReportViewSet.as_view({"get": "reports"})),
    path("admin/state/<int:pk>/resolve/", AdminReportViewSet.as_view({"post": "resolve_state"})),
    path("admin/user/<int:pk>/resolve/", AdminReportViewSet.as_view({"post": "resolve_user"})),
    path("admin/user/<int:pk>/delete/", AdminReportViewSet.as_view({"delete": "delete_user"})),
    path('', include(router.urls)),
]
