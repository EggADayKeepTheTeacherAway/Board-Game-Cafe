"""Views class for element that show to the user."""

from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import F, Count
from django.db.models.functions import ExtractWeekDay, ExtractHour
from django.views import generic
from django.utils import timezone
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
        """Sent data to the frontend."""
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
        REDIRECT_URL = redirect('board_game_cafe:rent')
        item_type = request.POST['item_type']
        item_id = request.POST['item_id']
        user = Customer.object.get(customer_id=request.session['customer_id'])
        due_date = request.POST['due_date']

        def table_handler():
            if (due_date - timezone.now()).hour > 6:
                messages.warning("You can rent table 6 hours at a time.")
                return REDIRECT_URL
            
            if Rental.objects.filter(customer=user,
                                     item_type="table").count() >= 1:
                messages.warning("You can rent 1 table at a time.")
                return REDIRECT_URL

        def boardgame_handler():
            if (due_date - timezone.now()).days > 9:
                messages.warning("You can rent boardgame 9 days at a time.")
                return REDIRECT_URL

            BoardGame.objects.get(boardgame_id=item_id).rent_boardgame()

        handler = {"Table": table_handler,
                   "BoardGame": boardgame_handler}
        
        response = handler.get(item_type)()
        if response is not None:
            return response

        Rental.objects.create(customer=user,
                                item_type=item_type,
                                item_id=item_id,
                                due_date=due_date)

    def get_queryset(self):
        """Sent data to the frontend."""
        return {
            'boardgame': BoardGame.objects.filter(stock__gt=0),
            'table': [table.table_id
                      for table in Table.objects.all()
                      if table.is_available()]
        }


class ReturnView(generic.ListView):
    """Class for display return page."""
    template_name = "app/return.html"
    context_object_name = 'data'

    def get(self, request, *args, **kwargs):
        self.user = Customer.objects.get(customer_id=request.session['customer_id'])
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        rental = Rental.objects.get(rental_id=request.POST['rental_id'])
        rental_fee = rental.compute_fee() # TODO: if have transaction THIS IS THE FEE.
        if rental.item_type == 'BoardGame':
            rental.get_item().return_boardgame()

    def get_queryset(self):
        """Sent data to the frontend."""
        return {
            'boardgame': Rental.objects.filter(customer=self.user, item_type="BoardGame",
                                               status='rented'),
            'table': Rental.objects.filter(customer=self.user, item_type="Table",
                                           status='rented'),
        }


class StatView(generic.ListView):
    """Class for display statistic of many thing."""
    template_name = "app/statistic.html"
    context_object_name = 'data'

    def get_queryset(self):
        """Sent data to the frontend."""
        popular_boardgame = (
            Rental.objects.filter(item_type="BoardGame")
            .values('item_id')
            .annotate(rental_count=Count('item_id'))
            .order_by('-rental_count')
            .values_list('item_id', flat=True)
                        )
        
        peak_hour = (
            Rental.objects.filter(item_type="Table")
            .annotate(hour=ExtractHour('rent_date'))
            .values('hour')
            .annotate(table_rental=Count('hour'))
            .order_by('-table_rental')
            .values_list('hour', flat=True)
        )
        week_day = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        peak_day = (
            Rental.objects.filter(item_type="Table")
            .annotate(day=ExtractWeekDay('rent_date'))  # Extract weekday from rent_date
            .values('day')
            .annotate(table_rental=Count('day'))
            .order_by('-table_rental')
            .values_list('day', flat=True)  # Get only the day
        )

        print('hnelo')
        print(popular_boardgame)
        print(peak_hour)
        print(peak_day)

        try:
            output = {
                "popular_boardgame": BoardGame.objects.get(boardgame_id=popular_boardgame[0]),
                "top_boardgame": BoardGame.objects.filter(boardgame_id__in=popular_boardgame[:5]),
                "peak_hour": peak_hour[0],
                "peak_day": week_day[peak_day[0]],
            }

        except (IndexError, BoardGame.DoesNotExist):
            return None

        return output


class ProfileView(generic.ListView):
    """Class for display the profile of customer."""
    template_name = "app/profile.html"
    context_object_name = 'data'

    def get(self, request, *args, **kwargs):
        self.user = Customer.objects.get(customer_id=request.session['customer_id'])
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """Sent data to the frontend."""
        return {
            'id': self.user.customer_id,
            'username': self.user.customer_name,
            'contact': self.user.contact,
            'total_fee': sum(Rental.objects.filter(customer=self.user,
                                         status='returned').values_list('fee', flat=True))
        }
    