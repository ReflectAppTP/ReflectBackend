from django.urls import path
from . import views
from .views import UpdateVisibilityView, UserDetailWithStateView, StreakView, UpdateUsernameView, ChangePasswordView, \
    DeleteAccountView, UpdatePremiumView

urlpatterns = [
    path('<int:user_id>/', views.profile, name='profile'),
    path("user/<int:user_id>/", UserDetailWithStateView.as_view()),
    path('user/streak/', StreakView.as_view()),
    path("user/update/visibility/", UpdateVisibilityView.as_view()),
    path("user/update/premium/", UpdatePremiumView.as_view()),
    path("user/update/username/", UpdateUsernameView.as_view()),
    path("user/update/password/", ChangePasswordView.as_view()),
    path("user/delete/", DeleteAccountView.as_view()),
]