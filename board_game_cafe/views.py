"""Views class for element that show to the user."""

from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import F, Count
from django.views import generic
from django.utils import timezone
from .forms import RegisterForm, LoginForm
from .models import (Rental, Table, BoardGame,
                     Customer, BoardGameCategory,
                     BoardGameGroup,
                     )


def login(request):
    """Login function."""
    if request.method == "POST":
        customer_name = request.POST['customer_name']
        password = request.POST['password']
        user = Customer.objects.filter(customer_name=customer_name, password=password)
        if user.exists():
            user = user.get()
            request.session['customer_id'] = user.customer_id 
            return redirect('board_game_cafe:index')
        messages.error(request,
                       "You entered wrong username or password.")

        return redirect('signup')
    return render(request, 'signup.html')


def signup(request):
    """Sign up function."""
    if request.method == "POST":
        customer_name = request.POST['customer_name']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        contact = request.POST['contact']

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('signup')

        if Customer.objects.filter(customer_name=customer_name).exists():
            messages.warning(request, "You already have an account.")
            return redirect('signup')

        user = Customer.objects.create(customer_name=customer_name,
                                       password=password,
                                       contact=contact)

        request.session['customer_id'] = user.customer_id
        messages.success(request, "Account created successfully!")
        return redirect('board_game_cafe:index')

    return render(request, 'signup.html')

def logout(request):
    """Logout function."""
    if 'customer_id' in request.session:
        del request.session['customer_id']
        messages.success(request, "You have been logged out successfully.")
    else:
        messages.warning(request, "You are not logged in.")
    return redirect('signup')


class HomeView(generic.ListView):
    """Class for display Home page."""
    template_name = "app/index.html"
    context_object_name = "data"

    def get_queryset(self):

        return {
            'boardgame': BoardGame.objects.all(),
            'table': Table.objects.all()
            }


class RentView(generic.ListView):
    """Class for display rent page."""
    model = Rental
    template_name = "app/rent.html"

    context_object_name = 'item'

    def post(self, request, *args, **kwargs):
        item_type = request.POST['item_type']
        item_id = request.POST['item_id']
        user = Customer.object.get(customer_id=request.session['customer_id'])
        due_date = request.POST['due_date']

        if (due_date - timezone.now()).days > 9:
            messages.warning("You can rent boardgame 9 days at a time.")
            return redirect('board_game_cafe:rent')

        if item_type == 'BoardGame':
            BoardGame.objects.get(boardgame_id=item_id).rent_boardgame()

        Rental.objects.create(customer=user,
                                item_type=item_type,
                                item_id=item_id,
                                due_date=due_date)

    def get_queryset(self):
        return {
            'boardgame': BoardGame.objects.filter(stock__gt=0),
            'table': [table.table_id
                      for table in Table.objects.all()
                      if table.is_available()]
        }


class ReturnView(generic.ListView):
    """Class for display return page."""
    template_name = "app/return.html"

    def get(self, request, *args, **kwargs):
        self.user = Customer.objects.get(customer_id=request.session['customer_id'])
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        rental = Rental.objects.get(rental_id=request.POST['rental_id'])
        rental_fee = rental.compute_fee() # TODO: if have transaction THIS IS THE FEE.
        if rental.item_type == 'BoardGame':
            rental.get_item().return_boardgame()

    def get_queryset(self):
        return Rental.objects.filter(customer=self.user, status='rented')


class StatView(generic.ListView):
    """Class for display statistic of many thing."""
    template_name = "app/statistic.html"

    def get_queryset(self):
        return []


class ProfileView(generic.ListView):
    """Class for display the profile of customer."""
    template_name = "app/profile.html"

    def get_queryset(self):
        popular_boardgame = (
            Rental.objects.filter(item_type="BoardGame")
            .values('item_id')
            .annotate(rental_count=Count('item_id'))
            .order_by('-rental_count')
            .values_list('item_id')
                        )
        
        peak_hour = (
            Rental.objects.filter(item_type="Table")
            .values(hour=F('rent_date__hour'))
            .annotate(table_rental=Count('hour'))
            .order_by('-hour')
            .values_list('hour')
        )
        week_day = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        peak_day = (
            Rental.objects.filter(item_type="Table")
            .values(day=F('rent_date__weekday'))
            .annotate(table_rental=Count('day'))
            .order_by('-day')
            .values_list('day')
        )

        return {
            "popular_boardgame": BoardGame.objects.get(boardgame_id=popular_boardgame[0]),
            "top_boardgame": BoardGame.objects.filter(boardgame_id__in=popular_boardgame[:5]),
            "peak_hour": peak_hour[0],
            "peak_day": week_day[peak_day[0]],
        }
    