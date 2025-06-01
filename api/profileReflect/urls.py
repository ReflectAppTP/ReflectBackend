from django.urls import path
from . import views
from .views import UpdateVisibilityView, UserDetailWithStateView

urlpatterns = [
    path('<int:user_id>/', views.profile, name='profile'),
    path('user/visibility/', UpdateVisibilityView.as_view()),
    path("user/<int:user_id>/", UserDetailWithStateView.as_view()),
]