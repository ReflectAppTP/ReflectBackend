from django.urls import path
from .views import AdminReportViewSet

admin_reports = AdminReportViewSet.as_view({
    "get": "reports",
    "post": "resolve_state",
})

urlpatterns = [
    path("admin/users/", AdminReportViewSet.as_view({"get": "users"})),
    path("admin/reports/", AdminReportViewSet.as_view({"get": "reports"})),
    path("admin/state/<int:pk>/resolve/", AdminReportViewSet.as_view({"post": "resolve_state"})),
    path("admin/user/<int:pk>/resolve/", AdminReportViewSet.as_view({"post": "resolve_user"})),
    path("admin/user/<int:pk>/delete/", AdminReportViewSet.as_view({"delete": "delete_user"})),
]
