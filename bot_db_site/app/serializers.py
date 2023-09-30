from rest_framework import serializers
from .models import TelegramChat


class TelegramChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramChat
        fields = '__all__'

