from django.contrib import admin
from django.urls import path, include
from app.views import TelegramChatView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('rest_framework.urls')),
    path('api/v1/chat/', TelegramChatView.as_view()),
    path('api/v1/chat/<int:telegram_chat_id>/', TelegramChatView.as_view()),
]
