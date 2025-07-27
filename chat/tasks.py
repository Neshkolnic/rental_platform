# chat/tasks.py
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@shared_task
def send_system_notification(chat_id, text):
    """
    Отправляем сообщение в указанный чат через WebSocket.
    """
    channel_layer = get_channel_layer()
    group_name = f'chat_{chat_id}'
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'chat_message',
            'message': text,
            'sender': 'Система',
            'created_at': '',
        }
    )
