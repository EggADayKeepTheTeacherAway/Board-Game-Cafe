from django.db import models

# Create your models here.
class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True, unique=True)
    customer_name = models.CharField(max_length=30, default=None)
    contact = models.CharField(max_length=30, default=None)


class Booking(models.Model):
    booking_id = models.AutoField(primary_key=True, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    item_type = models.CharField(max_length=30, default=None)
    item_id = models.CharField(max_length=30, default=None)


class Rental(models.Model):
    rental_id = models.AutoField(primary_key=True, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    item_type = models.CharField(max_length=30, default=None)
    item_id = models.CharField(max_length=30, default=None)
    rent_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()