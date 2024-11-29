from celery import shared_task
from datetime import timedelta
from django.utils.timezone import now
from .models import Rental

@shared_task
def delete_expired_rentable_bookings():
    three_days_ago = now() - timedelta(days=3)
    Rental.objects.filter(status='rentable', rent_date__lte=three_days_ago).delete()
