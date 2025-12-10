from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from .models import TgUser
from .serializers import TgUserVerifySerializer
from .tg.client import TgClient


class TgUserVerifyView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TgUserVerifySerializer

    def patch(self, request: Request, *args, **kwargs) -> Response:
        """Обрабатка запроса для верификации пользователя Telegram"""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code: str = serializer.validated_data.get('verification_code')

        try:
            tg_user: TgUser = TgUser.objects.select_related('user').get(verification_code=code)
            if tg_user.user is not None and tg_user.user != request.user:
                return Response({"error": "Код уже используется другим пользователем"}, status=400)
            if TgUser.objects.filter(user=request.user).exclude(pk=tg_user.pk).exists():
                return Response({"error": "Ваш аккаунт уже привязан к другому Telegram"}, status=400)

            tg_user.user = request.user
            tg_user.save(update_fields=['user'])

            TgClient().send_message(
                tg_user.telegram_chat_id,
                "Аккаунт успешно привязан к пользователю @" + request.user.username)

            return Response({
                "success": True,
                "telegram_user": {
                    "id": tg_user.telegram_user_id,
                    "username": tg_user.username,
                    "chat_id": tg_user.telegram_chat_id
                }
            })

        except TgUser.DoesNotExist:
            return Response({"error": "Неверный код"}, status=400)
