from django.utils import timezone
from django.contrib import messages
from board_game_cafe.models import Booking, Table, BoardGame


class Booker:
    """
    Booking works as follows:
        -Boardgame
            1. If BoardGame is available, booking's status will be `rentable` and boardgame stock deducted.
            2. If BoardGame is not available, booking's status will be `booked` and boardgame stock not deducted.
            3. If BoardGame was returned while there are Bookings for the boardgame, oldest booking's status will be `rentable`, and boardgame stock deducted.

        -Table
            1. If Table is available, booking will not be created but rental for the table instead.
            2. If Table is not available, booking will wait until current user returns
    Remarks:
        boardgame available: stock > 0
        table available: table is not being rented
    """
    @classmethod
    def book_table(cls, request, item_id, user):
        booking = Booking.create_or_delete(item_type="Table", item_id=item_id, user=user)
        if booking is None:
            messages.info(request, "Booking for Table has been cancelled.")
            return
        if Table.objects.get(table_id=item_id).is_available():
            booking.status = 'rentable'
            booking.rentable_date = timezone.now()
            booking.save()
        messages.info(request, "Booking for Table was created successfully.")


    @classmethod
    def book_boardgame(cls, request, item_id, user):
        booking = Booking.create_or_delete(item_type="BoardGame", item_id=item_id, user=user)
        if booking is None:
            return
        boardgame = BoardGame.objects.get(boardgame_id=item_id)
        if boardgame.stock > 0:
            boardgame.stock -= 1
            booking.status = "rentable"
            booking.rentable_date = timezone.now()
            boardgame.save()


    @classmethod
    def get_booker(cls, item_type):
        return {"Table": cls.book_table,
                "BoardGame": cls.book_boardgame}.get(item_type)()