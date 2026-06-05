from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, RegisterAPIView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='user_register'),
] + router.urls
