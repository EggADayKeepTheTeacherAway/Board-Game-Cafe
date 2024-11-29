from celery import shared_task
from django.utils.timezone import now, timedelta
from .models import Booking

@shared_task
def delete_expired_rentable_bookings():
    three_days_ago = now() - timedelta(days=3)
    Booking.objects.filter(status='rentable', rent_date__lte=three_days_ago).delete()
