# context_processor.py
from .models import Message

def unread_messages(request):
    if request.user.is_authenticated:
        unread = Message.objects.filter(receiver=request.user, is_read=False).order_by('-timestamp')
        return {'unread_messages': unread}  # Changed key
    return {'unread_messages': []}  # Changed key