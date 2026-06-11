from django.urls import path
from .views import profile, admin_only


urlpatterns = [
    path("profile/", profile, name="profile"),
    path("admin-only/", admin_only, name="admin_only"),
] 
