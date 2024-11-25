from django.db import models
from django.utils import timezone

# Create your models here.
class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True, unique=True)
    customer_name = models.CharField(max_length=30, default=None)
    contact = models.CharField(max_length=30, default=None)

    class Meta:
        app_label = 'board_game_cafe'
        db_table = 'Customer'


class Booking(models.Model):
    booking_id = models.AutoField(primary_key=True, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    item_type = models.CharField(max_length=30, default=None)
    item_id = models.CharField(max_length=30, default=None)
    
    class Meta:
        app_label = 'board_game_cafe'
        db_table = 'Booking'


class Rental(models.Model):
    rental_id = models.AutoField(primary_key=True, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    item_type = models.CharField(max_length=30, default=None)
    item_id = models.CharField(max_length=30, default=None)
    rent_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField(default=timezone.now+timezone.timedelta(days=3))
    status = models.CharField(max_length=30, default=None)

    @property
    def duration(self):
        return timezone.now() - self.rent_date

    class Meta:
        app_label = 'board_game_cafe'
        db_table = 'Rental'


class Table(models.Model):
    table_id = models.AutoField(primary_key=True, unique=True)
    capacity = models.IntegerField(default=4)


class BoardGameGroup(models.Model):
    group_name = models.Charfield(max_length=30, default="small")
    base_fee = models.IntegerField(default=5)


class BoardGame(models.Model):
    boardgame_id = models.AutoField(primary_key=True, unique=True)
    boardgame_name = models.CharField(max_length=30, default=None)
    category_id = models
    group = models.ForeignKey(BoardGameGroup)
