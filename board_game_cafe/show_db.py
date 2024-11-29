import os
import django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django.setup()

from board_game_cafe.models import Rental

for rental in Rental.objects.all():
    print(f"{rental.item_type: <10} {rental.customer.customer_name: <10} {rental.rent_date: <10} {rental.due_date: <10}")