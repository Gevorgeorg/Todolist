from django.urls import path
from . import views

urlpatterns = [
    path('login', views.LoginView.as_view(), name='login'),
    path('signup', views.SignupView.as_view(), name='signup'),
    path('profile', views.ProfileView.as_view(), name='profile'),
    path('update_password', views.UpdatePasswordView.as_view(), name='update_password'),
    path('social-success', views.SocialAuthSuccessView.as_view(), name='social_success'),
    path('social-error', views.SocialAuthErrorView.as_view(), name='social_error'),

]
