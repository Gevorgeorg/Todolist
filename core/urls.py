from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from . import views
from .views import UserViewSet, CustomLoginView, CustomTokenObtainPairView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # JWT эндпоинты
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

# Эндпоинты для фронта
    path('signup', views.UserViewSet.as_view({'post': 'create'}), name='signup'),
    #path('login', TokenObtainPairView.as_view(), name='login'),
    path('profile', views.UserViewSet.as_view({'get': 'me'}), name='profile'),
    path('', include(router.urls)),
    #path('login', CustomLoginView.as_view(), name='custom_login'),
    path('login', CustomTokenObtainPairView.as_view(), name='custom_login'),


]

