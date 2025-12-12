from django.urls import path
from .views import TgUserVerifyView

urlpatterns = [path('verify', TgUserVerifyView.as_view(), name='bot_verify'), ]
