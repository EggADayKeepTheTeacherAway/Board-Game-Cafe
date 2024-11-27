from board_game_cafe.models import Rental

for rental in Rental.objects.all():
    print(f"{rental.item_type: <10} {rental.customer.customer_name: <10}")