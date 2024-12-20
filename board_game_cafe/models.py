from django.db import models
from django.utils import timezone
from django.db.models import F, Q, Count, OuterRef, Subquery
from math import ceil


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True, unique=True)
    customer_name = models.CharField(max_length=30, default=None, unique=True)
    contact = models.CharField(max_length=30, default=None)
    password = models.CharField(max_length=30, default=None)

    class Meta:
        app_label = 'board_game_cafe'
        db_table = 'Customer'


class Booking(models.Model):
    booking_id = models.AutoField(primary_key=True, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    item_type = models.CharField(max_length=30, default=None)
    item_id = models.CharField(max_length=30, default=None)
    status = models.CharField(max_length=30, default='booked')
    rentable_date = models.DateTimeField(null=True)
    
    @classmethod
    def update_queue(cls, item_type, item_id, user, *args, **kwargs):
        next_booking_in_queue = Booking.get_next_in_queue(item_type, item_id)
        if next_booking_in_queue:
            next_booking_in_queue.delete()
            if item_type == "BoardGame":
                BoardGame.objects.get(boardgame_id=item_id).stock -= 1
            Rental.objects.create(customer=user,
                                    item_type=item_type,
                                    item_id=item_id,
                                    due_date={"Table": timezone.now()+timezone.timedelta(hours=6),
                                            "BoardGame": timezone.now()+timezone.timedelta(days=3)}.get(item_type)
                                    )

    @classmethod
    def delete_if_exists(cls, item_type, item_id, user):
        booking_for_this_obj = Booking.objects.filter(item_id=item_id,
                                item_type=item_type,
                                customer=user)
        if booking_for_this_obj.exists():
            booking_for_this_obj.get().delete()

        if item_type == "BoardGame":
            BoardGame.objects.get(boardgame_id=item_id).return_boardgame()

    @classmethod
    def get_next_in_queue(cls, item_type, item_id):
        return Booking.objects.filter(item_type=item_type, item_id=item_id, status='booked').order_by('booking_id').first()

    @classmethod
    def create_or_delete(cls, item_type, item_id, user):
        booking = Booking.objects.filter(item_type=item_type, item_id=item_id, customer=user)
        if booking.exists():
            booking.delete()
            return
        return Booking.objects.create(item_type=item_type, item_id=item_id, customer=user)

    class Meta:
        app_label = 'board_game_cafe'
        db_table = 'Booking'


def next_three_days():
    return timezone.now() + timezone.timedelta(days=3)


class Rental(models.Model):
    rental_id = models.AutoField(primary_key=True, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    item_type = models.CharField(max_length=30, default=None)
    item_id = models.CharField(max_length=30, default=None)
    rent_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField(default=next_three_days)
    status = models.CharField(max_length=30, default='rented')
    return_date = models.DateTimeField(null=True)
    fee = models.IntegerField(null=True)

    @property
    def duration(self) -> int:
        if self.item_type == 'Table':
            return ceil((timezone.now() - self.rent_date).total_seconds()/3600)
        return ceil((timezone.now() - self.rent_date).total_seconds()/(3600*24))

    @classmethod
    def can_rent(cls, user, item_type):
        item = {'Table': Table, 'BoardGame': BoardGame}.get(item_type)
        return Rental.objects.filter(customer=user,
                    item_type=item_type, status='rented').count() < item.max_rent

    @classmethod
    def create(cls, item_type, item_id, user, due_date):
        Booking.delete_if_exists(item_type, item_id, user)
        day_or_hour = 'hours' if item_type == 'Table' else 'days'
        item = {'Table': Table, 'BoardGame': BoardGame}.get(item_type)
        if not Rental.is_good_due_date(due_date, item_type):
            message = f"You can rent {item_type.lower()} {item.max_rent_time} {day_or_hour} at a time."
            status = 'failed'
            
        if not Rental.can_rent(user, item_type):
            message = f"You can rent {item.max_rent} {item_type.lower()} at a time."
            status = 'failed'

        Rental.objects.create(customer=user,
                                item_type=item_type,
                                item_id=item_id,
                                due_date=due_date
                                )
        if item_type == 'BoardGame':
            BoardGame.objects.get(boardgame_id=item_id).rent_boardgame()

    def is_overdue(self):
        return not self.return_date or self.return_date > self.due_date

    def get_item(self):
        handle_item_type = {
                    "Table": lambda id: Table.objects.get(table_id=id),
                    "BoardGame": lambda id: BoardGame.objects.get(boardgame_id=id)}
        return handle_item_type[self.item_type](self.item_id)
    
    def compute_fee(self):
        self.fee = self.get_item().compute_fee(self.duration)
        self.status = 'returned'
        self.return_date = timezone.now()
        self.save()
        return self.fee

    class Meta:
        app_label = 'board_game_cafe'
        db_table = 'Rental'


class Table(models.Model):
    table_id = models.AutoField(primary_key=True, unique=True)
    capacity = models.IntegerField(default=4)

    max_rent_time = 6
    max_rent = 1
    
    @property
    def fee(self):
        return self.capacity*5
    
    @classmethod
    def can_rent(cls, user):        
        return Rental.objects.filter(customer=user,
                    item_type="Table", status='rented').count() < cls.max_rent
    
    @classmethod
    def get_sorted_data(cls, table_sort_mode, capacity):
        table_obj = Table.objects.all()
        if capacity:
            table_obj = table_obj.filter(capacity=capacity)
        if table_sort_mode:
            table_obj = table_obj.order_by(table_sort_mode)
        return table_obj

    def is_available(self, user):
        return str(self.table_id) not in set(Rental.objects.filter(
            item_type='Table', status="rented").values_list('item_id', flat=True))-\
                set(Booking.objects.filter(status="booked", item_type="Table", customer=user) or [])
    
    def compute_fee(self, hours):
        grace_period = min(hours, 6)
        return (
                hours * self.fee
              + max(0, self.fee*(hours-grace_period))
              )


class BoardGameGroup(models.Model):
    group_name = models.CharField(max_length=30, default="small")
    base_fee = models.IntegerField(default=5)
    num_player = models.CharField(max_length=30, default="1-4 people")


class BoardGameCategory(models.Model):
    category_id = models.AutoField(primary_key=True, unique=True)
    category_name = models.CharField(max_length=30, default="Dice")


class BoardGame(models.Model):
    boardgame_id = models.AutoField(primary_key=True, unique=True)
    boardgame_name = models.CharField(max_length=30, default=None)
    group = models.ForeignKey(BoardGameGroup, on_delete=models.CASCADE)
    category = models.ForeignKey(BoardGameCategory, on_delete=models.CASCADE)
    stock = models.IntegerField(default=0)

    max_rent_time = 9
    max_rent = 3

    @property
    def fee(self):
        return self.group.base_fee
    
    @classmethod
    def get_sorted_data(cls, boardgame_sort_mode, category):
        boardgame_obj = BoardGame.objects.all()
        if category:
            boardgame_category = BoardGameCategory.objects.get(category_name=category)
            boardgame_obj = boardgame_obj.filter(category=boardgame_category)
        if boardgame_sort_mode:
            if boardgame_sort_mode == 'A-Z':
                return boardgame_obj.order_by("boardgame_name")
            if boardgame_sort_mode == 'Popularity':
                active_rentals = Rental.objects.filter(
                    item_type="BoardGame",  # Only consider rentals for board games
                    item_id=OuterRef('boardgame_id')  # Match the item_id in Rental with boardgame_id in BoardGame
                ).values('item_id')  # Use item_id to count rentals

                # Now, annotate the BoardGame objects with the rental count
                boardgame_obj = BoardGame.objects.annotate(
                                    rental_count=Subquery(active_rentals.annotate(count=Count('item_id')).values('count')[:1])  # Count rentals
                                ).order_by('-rental_count')
        return boardgame_obj

    @classmethod
    def is_good_due_date(cls, due_date):
        return (due_date - timezone.now()).total_seconds()/(3600*24) < cls.max_rent_time
    
    @classmethod
    def can_rent(cls, user):
        return Rental.objects.filter(customer=user,
                    item_type="BoardGame", status='rented').count() < cls.max_rent
    
    def is_available(self):
        return self.stock > 0

    def rent_boardgame(self):
        if self.stock <= 0:
            raise ValueError("This BoardGame is not available at this time")
        self.stock -= 1
        self.save()

    def return_boardgame(self):
        self.stock += 1
        self.save()

    def compute_fee(self, days):
        grace_period = min(self.max_rent_time, days)
        return (
                days * self.fee
              + max(0, self.fee*(days-grace_period))
              )
    
   