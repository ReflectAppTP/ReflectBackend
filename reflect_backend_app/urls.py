from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/authReflect/', include('api.authReflect.urls')),
    path('api/emotions/', include('api.emotions.urls')),
]