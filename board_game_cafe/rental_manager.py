from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.utils.timezone import make_aware
from django.utils import timezone
from .models import Rental, BoardGame, Booking

import datetime


class Renter:
    @classmethod
    def rent_table(cls, request, user, item_id, *args, **kwargs ):
        if Rental.objects.filter(item_type='Table', status='rented', customer=user).count() >= 1:
            messages.warning(request, "You can rent 1 table at a time.")
            return
        
        Rental.objects.create(customer=user,
                            item_type="Table",
                            item_id=item_id,
                            due_date=timezone.now()+timezone.timedelta(hours=6)
                            )
        
        messages.info(request, "Your rental order has been created.")


    @classmethod
    def rent_boardgame(cls, request, user, item_id, due_date, *args, **kwargs):
        try:
            due_date = make_aware(datetime.datetime.strptime(due_date, "%Y-%m-%d"))
        except ValueError:
            messages.error(request, "Invalid due date format. Please use YYYY-MM-DD.")
            return

        if not BoardGame.is_good_due_date(due_date):
            messages.warning(request, f"You can rent BoardGame {BoardGame.max_rent_time} days at a time.")
            return
            
        if not BoardGame.can_rent(user):
            messages.warning(request, f"You can rent {BoardGame.max_rent} boardgames at a time.")
            return
        
        try:
            BoardGame.objects.get(boardgame_id=item_id).rent_boardgame()
        except ValueError:
            messages.warning(request, "This BoardGame has ran out of stock at the moment.")
            return

        Rental.objects.create(customer=user,
                                item_type="BoardGame",
                                item_id=item_id,
                                due_date=due_date
                                )
        
        messages.info(request, "Your rental order has been created.")
    
    @classmethod
    def run_renter(cls, item_type, *args, **kwargs):
        return {"Table": cls.rent_table,
                "BoardGame": cls.rent_boardgame}.get(item_type)(item_type=item_type, *args, **kwargs)
    