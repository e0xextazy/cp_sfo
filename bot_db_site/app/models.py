from django.db import models
import datetime

class TelegramChat(models.Model):
    chat_id = models.PositiveIntegerField(unique=True)
    chat_history = models.JSONField(default=list)

    def __str__(self):
        return str(self.chat_id)
    
    class Meta:
        indexes = [
            models.Index(fields=['chat_id'], name='chat_id_idx'),
        ]
