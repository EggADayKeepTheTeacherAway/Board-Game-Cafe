from django.db import models
from django.utils import timezone

# Create your models here.
class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True, unique=True)
    customer_name = models.CharField(max_length=30, default=None)
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
    status = models.CharField(max_length=30, default=None)
    
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
        return (timezone.now() - self.rent_date).days

    def is_overdue(self):
        return not self.return_date or self.return_date > self.due_date

    def compute_fee(self):
        fee_handler = {"Table": 5,
               "BoardGame": BoardGame.objects.get(
                   boardgame_id=self.item_id).group.base_fee
               }
        fee = self.duration * fee_handler[self.item_type]
        fee += max(0, fee_handler[self.item_type]*(self.duration-9)) # compute overdue fee
        self.fee = fee
        self.status = 'returned'
        self.return_date = timezone.now()
        self.save()

    def get_item(self):
        handle_item_type = {"Table": lambda id: Table.objects.get(table_id=id),
                     "BoardGame": lambda id: BoardGame.objects.get(boardgame_id=id)}
        
        return handle_item_type[self.item_type](self.item_id)

    class Meta:
        app_label = 'board_game_cafe'
        db_table = 'Rental'


class Table(models.Model):
    table_id = models.AutoField(primary_key=True, unique=True)
    capacity = models.IntegerField(default=4)

    def is_available(self):
        return self.table_id not in Rental.objects.filter(
            item_type='Table', status="rented").values_list('item_id', flat=True)


class BoardGameGroup(models.Model):
    group_name = models.CharField(max_length=30, default="small")
    base_fee = models.IntegerField(default=5)

class BoardGameCategory(models.Model):
    category_id = models.AutoField(primary_key=True, unique=True)
    category_name = models.CharField(max_length=30, default="Dice")

class BoardGame(models.Model):
    boardgame_id = models.AutoField(primary_key=True, unique=True)
    boardgame_name = models.CharField(max_length=30, default=None)
    group = models.ForeignKey(BoardGameGroup, on_delete=models.CASCADE)
    category = models.ForeignKey(BoardGameCategory, on_delete=models.CASCADE)
    stock = models.IntegerField(default=0)

    def rent_boardgame(self):
        if self.stock <= 0:
            raise ValueError("This BoardGame is not available at this time")
        self.stock -= 1
        self.save()

    def return_boardgame(self):
        self.stock += 1
        self.save()