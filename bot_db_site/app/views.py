from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TelegramChat
from django.shortcuts import get_object_or_404
import pytz

class TelegramChatView(APIView):

    def get(self, request, telegram_chat_id, format=None):
        telegram_chat = get_object_or_404(TelegramChat, telegram_chat_id=telegram_chat_id)
        data = {
            "telegram_chat_id": telegram_chat_id,
            "answers": telegram_chat.answers,
            "questions": telegram_chat.questions,
            "time": telegram_chat.timestamp.astimezone(pytz.timezone('Asia/Irkutsk')).strftime('%Y-%m-%d %H:%M:%S')
        }
        return Response(data, status=status.HTTP_200_OK)
    
    def post(self, request, format=None):
        telegram_chat_id = request.data.get("telegram_chat_id")
        text = request.data.get("question") or request.data.get("answer")
        
        if not telegram_chat_id or not text:
            return Response(
                {"error": "Both telegram_chat_id and either question or answer are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        telegram_chat, created = TelegramChat.objects.get_or_create(telegram_chat_id=telegram_chat_id)
        
        if "question" in request.data:
            telegram_chat.questions.append(text)
        if "answer" in request.data:
            telegram_chat.answers.append(text)
        
        telegram_chat.save()
        
        return Response({"message": "Record updated successfully."}, status=status.HTTP_200_OK)
    
    def delete(self, request, telegram_chat_id, format=None):
        telegram_chat = get_object_or_404(TelegramChat, telegram_chat_id=telegram_chat_id)
        telegram_chat.delete()
        return Response({"message": "Record deleted successfully."}, status=status.HTTP_204_NO_CONTENT)