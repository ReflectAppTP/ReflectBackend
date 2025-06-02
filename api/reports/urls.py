from django.urls import path, include
from .views import AdminReportViewSet, AdminUserUpdateView
from rest_framework.routers import DefaultRouter
from .views import UserReportViewSet, StateReportViewSet, BlockUserView

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
    path("admin/user/<int:user_id>/block/", BlockUserView.as_view()),
    path('admin/user/<int:user_id>/edit/username/', AdminUserUpdateView.as_view()),
    path('admin/user/<int:user_id>/edit/is_blocked/', AdminUserUpdateView.as_view()),
    path('admin/user/<int:user_id>/edit/is_admin/', AdminUserUpdateView.as_view()),
    path("", include(router.urls)),
]
