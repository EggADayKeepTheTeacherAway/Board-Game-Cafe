from django.utils import timezone
from django.contrib import messages
from board_game_cafe.models import Booking, Table, BoardGame


class Booker:
    """
    Booking works as follows:
        -Boardgame
            1. If BoardGame is available, booking's status will be `rentable` and boardgame stock deducted.
            2. If BoardGame is not available, booking's status will be `booked` and boardgame stock not deducted.
            3. If BoardGame was returned while there are Bookings for the boardgame, oldest booking's will be deleted,
               and new Rental will be created (its due_date will be 3 days after Rental creation), boardgame stock deducted.

        -Table
            1. If Table is available, booking will not be created but rental for the table instead.
            2. If Table is not available, booking will wait until current user returns and rent right after them with added travel time (1 hour).
    Remarks:
        boardgame available: stock > 0
        table available: table is not being rented
    """
    @classmethod
    def book_boardgame(cls, request, item_id, user) -> None:
        booking = Booking.create_or_delete(item_type="BoardGame", item_id=item_id, user=user)
        boardgame = BoardGame.objects.get(boardgame_id=item_id)
        if booking is None:
            boardgame.return_boardgame()
            messages.info(request, "Booking for BoardGame has been cancelled.")
            return
        next_in_queue = Booking.get_next_in_queue("BoardGame", item_id)

        if boardgame.is_available():
            boardgame.rent_boardgame()
            booking.status = "rentable"
            booking.rentable_date = timezone.now()
            booking.save()
            return

        messages.info(request, "Booking for BoardGame was created successfully.")

    @classmethod
    def book_table(cls, request, item_id, user):
        booking = Booking.create_or_delete(item_type="Table", item_id=item_id, user=user)
        if booking is None:
            messages.info(request, "Booking for Table has been cancelled.")
            return
        
        table = Table.objects.get(table_id=item_id)
        if table.is_available(user):
            booking.status = 'rentable'
            booking.rentable_date = timezone.now()
            booking.save()
        
        messages.info(request, "Booking for Table was created successfully.")


    @classmethod
    def run_booker(cls, item_type, request, item_id, user):
        return {"Table": cls.book_table,
                "BoardGame": cls.book_boardgame}.get(item_type)(request=request, item_id=item_id, user=user)