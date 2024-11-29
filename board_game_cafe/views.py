"""Views class for element that show to the user."""

from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import F, Count
from django.db.models.functions import ExtractWeekDay, ExtractHour
from django.views import generic
from django.utils import timezone
from datetime import datetime
from django.utils.timezone import make_aware, now
from unicodedata import category

from .models import (Rental, Table, BoardGame,
                     Customer, BoardGameCategory,
                     BoardGameGroup, Booking
                     )
from .rental_manager import Renter
from .booking_manager import Booker

def normalize_data(data):
    post_data = {}
    for key, val in data.items():
        if val == 'none':
            post_data[key] = ''
            continue
        post_data[key] = val
    print(post_data)
    return post_data


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

        if len(contact) != 10:
            messages.warning(request, "Invalid contact number")
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

    def post(self, request, *args, **kwargs):
        """
        POST DATA SCHEMA:
        {
            item_type: str['Table' || 'BoardGame']
            item_id: str|int

            boardgame_sort_mode: str['A-Z' || 'Popularity']
            boardgame_filter: str
            table_sortt_mode: str
            table_filter: str
        }
        """

        post_data = normalize_data(request.POST)

        user = Customer.objects.get(customer_id=request.session['customer_id'])
        item_type = post_data.get('item_type')
        item_id = post_data.get('item_id')
        boardgame_sort_mode = post_data.get('boardgame_sort_mode')
        category = post_data.get('boardgame_filter')
        table_sort_mode = post_data.get('table_sort_mode')
        capacity = post_data.get('table_filter')

        if item_type and item_id:
            Booker.run_booker(item_type=item_type, request=request, item_id=item_id, user=user)

        
        return render(request, 'app/index.html', context={'data': self.get_queryset(boardgame_sort_mode=boardgame_sort_mode,
                                                                                            category=category,
                                                                                            table_sort_mode=table_sort_mode,
                                                                                            capacity=capacity)})

    def get_queryset(self, boardgame_sort_mode='', category='', table_sort_mode='', capacity='', *args, **kwargs):
        """
        Return dict consists of 2 datas: `boardgame`, and `table`.
        
        context_object_name = `data`

        data = {
            boardgame: [`BoardGame.objects`]
            table: [`Table.objects`]
        }
        """
        not_available = BoardGame.objects.filter(stock=0).values_list('boardgame_id', flat=True)
        num_max = max([table.capacity for table in Table.objects.all()])
        category_list = []
        for board in BoardGame.objects.all():
            if board.category.category_name not in category_list:
                category_list.append(board.category.category_name)

        return {
            'boardgame': BoardGame.get_sorted_data(boardgame_sort_mode=boardgame_sort_mode, category=category),
            'table': Table.get_sorted_data(table_sort_mode=table_sort_mode, capacity=capacity),
            'list_of_capacity': [i for i in range(1, num_max + 1)],
            'list_of_category': category_list,
            }


class RentView(generic.ListView):
    """Class for display rent page."""
    model = Rental
    template_name = "app/rent.html"

    context_object_name = 'item'

    def __init__(self):
        """Initailize method for Rent feature."""
        super().__init__()
        self.user = None

    def get(self, request, *args, **kwargs):
        self.user = Customer.objects.get(customer_id=request.session['customer_id'])
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        POST DATA SCHEMA:
        {
            what_do: str['sort' || 'rent']

            item_type: str['Table' || 'BoardGame']
            item_id: str|int
            due_date: Datetime? idk you tell me or give whatever I'll convert it

            boardgame_sort_mode: str['A-Z' || 'Popularity']
            boardgame_filter: str
            table_sortt_mode: str
            table_filter: str
        }
        """

        post_data = normalize_data(request.POST)

        redirect_url = redirect('board_game_cafe:rent')
        
        item_type = post_data['item_type']
        item_id = post_data['item_id']
        due_date = post_data['due_date']
        user = Customer.objects.get(customer_id=request.session['customer_id'])
        
        Booking.delete_if_exists(item_type, item_id, self.user)

        Renter.run_renter(request=request, item_type=item_type, item_id=item_id, user=user, due_date=due_date)

        return redirect_url

        
    def get_queryset(self):
        """
        Return dict consists of 2 datas: `boardgame`, and `table`.
        
        context_object_name = `item`

        item = {
            boardgame: [`BoardGame.objects`]
            table: [`Table.objects`]
        }
        """
        renting = set(Rental.objects.filter(customer=self.user,
                                        status="rented", item_type="BoardGame").values_list('item_id', flat=True) or [])
        not_available = set(BoardGame.objects.filter(stock=0).values_list('boardgame_id', flat=True) or [])
        my_rentable_boardgame = set(Booking.objects.filter(status="rentable", item_type="BoardGame", customer=self.user) or [])
        exclude = set(renting).union(set(not_available)) - set(my_rentable_boardgame)

        return {
            'boardgame': BoardGame.objects.exclude(boardgame_id__in=exclude),
            'table': [table
                      for table in Table.objects.all()
                      if table.is_available(user=self.user)] + list(Booking.objects.filter(status='booked', item_type="Table", customer=self.user))
        }


class ReturnView(generic.ListView):
    """Class for display return page."""
    template_name = "app/return.html"
    context_object_name = 'data'

    def get(self, request, *args, **kwargs):
        self.user = Customer.objects.get(customer_id=request.session['customer_id'])
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        POST DATA SCHEMA:
        {
            item_id: str|int
            item_type: str
        }
        """

        post_data = normalize_data(request.POST)

        user = Customer.objects.get(customer_id=request.session['customer_id'])
        rental = Rental.objects.get(
            item_type=post_data['item_type'],
            item_id=post_data['item_id'],
            customer=user,
            status='rented'
        )

        item_type = rental.item_type
        item_id = rental.item_id
        rental_fee = rental.compute_fee()
        item = rental.get_item()
        if rental.item_type == 'BoardGame':
            item.return_boardgame()
        Booking.update_queue(item_type=item_type, item_id=item_id)
        rental.status = 'returned'
        rental.fee = rental_fee
        rental.return_date = timezone.now()
        rental.save()
        for rental in Rental.objects.all():
            print(f"{rental.item_type: <10} {rental.customer.customer_name: <10} {rental.rent_date: <10} {rental.due_date: <10}")
        messages.info(request, f"There is {rental_fee} Baht fee for your rental.")
        return redirect('board_game_cafe:return')

    def get_queryset(self, *args, **kwargs):
        """
        Return dict consists of 2 datas: `boardgame`, and `table`.
        
        context_object_name = `data`

        data = {
            boardgame: [`BoardGame.objects`]
            table: [`Table.objects`]
        }
        """
        user = kwargs.get('user')
        if user:
            self.user = user

        boardgame_rental = Rental.objects.filter(customer=self.user, item_type="BoardGame",
                                               status='rented')
        table_rental = Rental.objects.filter(customer=self.user, item_type="Table",
                                               status='rented')
        
        return {
            'boardgame': [boardgame.get_item() for boardgame in boardgame_rental],
            'table': [table.get_item() for table in table_rental],
        }


class StatView(generic.ListView):
    """Class for display statistic of many thing."""
    template_name = "app/statistic.html"
    context_object_name = 'data'

    def get_queryset(self):
        """
        Return dict consists of 4 datas: 
            `popular_boardgame`, `top_boardgame`, `peak_hour`, and `peak_day`.
        
        context_object_name = `data`

        data = {
            popular_boardgame: `BoardGame.objects`
            top_boardgame: [`BoardGame.objects`]
            peak_hour: int
            peak_day: str
        }
        """

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
            .values_list('hour', flat=True).first()
        )
        week_day = ["", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        peak_day = (
            Rental.objects.filter(item_type="Table")
            .annotate(day=ExtractWeekDay('rent_date'))  # Extract weekday from rent_date
            .values('day')
            .annotate(table_rental=Count('day'))
            .order_by('-table_rental')
            .values_list('day', flat=True)  # Get only the day
        ).first()

        if peak_day:
            peak_day_output = week_day[peak_day]
        else:
            peak_day_output = None

        try:
            popular =  BoardGame.objects.get(boardgame_id=popular_boardgame[0])
        except BoardGame.DoesNotExist:
            popular = None

        output = {
            "popular_boardgame":popular,
            "top_boardgame": BoardGame.objects.filter(boardgame_id__in=popular_boardgame[:5]),
            "peak_hour": peak_hour,
            "peak_day": peak_day_output,
        }


        return output


class ProfileView(generic.ListView):
    """Class for display the profile of customer."""
    template_name = "app/profile.html"
    context_object_name = 'data'

    def get(self, request, *args, **kwargs):
        self.user = Customer.objects.get(customer_id=request.session['customer_id'])
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return dict consists of 4 datas: 
            `id`, `username`, `contact`, and `total_fee`.
        
        context_object_name = `data`

        data = {
            id: int
            username: str
            contact: str
            total_fee: fee
        }
        """
        return {
            'id': self.user.customer_id,
            'username': self.user.customer_name,
            'contact': self.user.contact,
            'total_fee': sum(Rental.objects.filter(customer=self.user,
                                         status='returned').values_list('fee', flat=True))
        }
    