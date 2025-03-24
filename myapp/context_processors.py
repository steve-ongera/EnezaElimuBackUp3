from .models import Message
from django.contrib.auth.models import User

def unread_messages(request):
    if request.user.is_authenticated:
        messages = Message.objects.filter(receiver=request.user, is_read=False).order_by('-timestamp')
        return {'messages': messages}
    return {'messages': []}
