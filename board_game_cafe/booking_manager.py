from board_game_cafe.models import Booking


class Booker:
    @classmethod
    def book_table(cls, item_id, user):
        booking = Booking.create_or_delete(item_type="Table", item_id=item_id, user=user)
        if booking is None:
            return
        Booking.update_queue(item_type="Table", item_id=item_id)

