from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.signing import Signer
from .models import Member
from django.utils import timezone
from datetime import timedelta
import qrcode
from io import BytesIO
from django.core.files import File

@receiver(post_save, sender=Member)
def member_post_save(sender, instance, created, **kwargs):
    if created:
        update_fields = []
        if instance.plan and 'duration' in instance.plan.plan_type:
            instance.expiry_date = timezone.now().date() + timedelta(days=instance.plan.duration_days)
            update_fields.append('expiry_date')
        if instance.plan and 'session' in instance.plan.plan_type:
            instance.sessions_remaining = instance.plan.session_count
            update_fields.append('sessions_remaining')

        # Generate QR code
        signer = Signer()
        data = signer.sign(str(instance.id))

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        file_name = f'qr_{instance.id}.png'

        instance.qr_code.save(file_name, File(buffer), save=False)
        update_fields.append('qr_code')

        # Save again with the new fields.
        post_save.disconnect(member_post_save, sender=Member)
        instance.save(update_fields=update_fields)
        post_save.connect(member_post_save, sender=Member)
