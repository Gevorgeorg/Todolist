from rest_framework import serializers


class TgUserVerifySerializer(serializers.Serializer):
    verification_code = serializers.CharField(max_length=32, required=True, write_only=True)
