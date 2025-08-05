from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification

@receiver(post_save, sender=Notification)
def send_notification_on_save(sender, instance, created, **kwargs):
    if created:
        # Send real-time notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{instance.user.id}',
            {
                'type': 'send_notification',
                'message': instance.message,
            }
        )

        # Send email notification
        send_mail(
            f'New Notification: {instance.notification_type}',
            instance.message,
            'from@example.com',
            [instance.user.email],
            fail_silently=False,
        )
