from django.utils import timezone
from django.conf import settings

def handle_datetime(dt):
    if dt is None:
        return None
    if settings.USE_TZ:
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return timezone.localtime(dt)
    return dt
