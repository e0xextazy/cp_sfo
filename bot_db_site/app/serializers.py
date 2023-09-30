from rest_framework import serializers
from .models import TelegramChat


class ChatHistoryItemSerializer(serializers.Serializer):
    type = serializers.CharField()
    text = serializers.CharField()
    time = serializers.DateTimeField()

class TelegramChatSerializer(serializers.ModelSerializer):
    chat_history = ChatHistoryItemSerializer(many=True)

    class Meta:
        model = TelegramChat
        fields = ['chat_id', 'chat_history']