from django.db import models
import datetime

class TelegramChat(models.Model):
    telegram_chat_id = models.PositiveIntegerField(unique=True)
    questions = models.JSONField(default=list)
    answers = models.JSONField(default=list)
    timestamp = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.timestamp = datetime.datetime.now()
        super(TelegramChat, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.telegram_chat_id)
    
    class Meta:
        indexes = [
            models.Index(fields=['telegram_chat_id'], name='telegram_chat_id_idx'),
        ]
