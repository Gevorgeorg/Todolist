import uuid
from django.db import models
from core.models import User


class TgUser(models.Model):
    telegram_chat_id = models.BigIntegerField(unique=True)
    telegram_user_id = models.BigIntegerField(unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    verification_code = models.CharField(max_length=32, null=True, blank=True, unique=True)

    def generate_verification_code(self) -> str:
        """Генерация уникального кода верификации"""

        while True:
            code = str(uuid.uuid4()).replace('-', '')[:10].upper()
            if not TgUser.objects.filter(verification_code=code).exists():
                self.verification_code = code
                self.save(update_fields=['verification_code'])
                return code
