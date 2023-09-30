from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TelegramChat
from .serializers import TelegramChatSerializer
from django.shortcuts import get_object_or_404
import datetime
import pytz

class TelegramChatView(APIView):

    def get(self, request, chat_id):
        print(request.META.get('REMOTE_ADDR'))
        try:
            chat = TelegramChat.objects.get(chat_id=chat_id)
            serializer = TelegramChatSerializer(chat)
            return Response(serializer.data)
        except TelegramChat.DoesNotExist:
            return Response({"message": f"chat with chat_id={chat_id} not found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        print(request.META.get('REMOTE_ADDR'))
        data = request.data

        time_now = datetime.datetime.now().astimezone(pytz.timezone('Asia/Irkutsk')).strftime('%d-%m-%Y %H:%M:%S')
        
        chat_history_item = {
            'type': data.get('type', ''),
            'text': data.get('text', ''),
            'time': time_now,
        }

        chat_id = data['chat_id']
        chat, created = TelegramChat.objects.get_or_create(chat_id=chat_id)

        chat.chat_history.append(chat_history_item)
        chat.save()

        return Response({"message": f"successfully"}, status=status.HTTP_201_CREATED)

    
    def delete(self, request, chat_id):
        print(request.META.get('REMOTE_ADDR'))
        try:
            chat = TelegramChat.objects.get(chat_id=chat_id)
            chat.delete()
            return Response({"message": "successfully"}, status=status.HTTP_204_NO_CONTENT)
        except TelegramChat.DoesNotExist:
            return Response({"message": f"chat with chat_id={chat_id} not found"}, status=status.HTTP_404_NOT_FOUND)