"""Views class for element that show to the user."""

from datetime import datetime
from django.utils.timezone import make_aware
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import F, Count
from django.db.models.functions import ExtractWeekDay, ExtractHour
from django.views import generic
from django.utils import timezone
from datetime import datetime
from django.utils.timezone import make_aware, now
from .models import (Rental, Table, BoardGame,
                     Customer, BoardGameCategory,
                     BoardGameGroup, Booking
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

    def post(self, request, *args, **kwargs):
        """
        POST DATA SCHEMA:
        {
            boardgame_sort_mode: str['A-Z' || 'Popularity']
            boardgame_filter: str
            table_sortt_mode: str
            table_filter: str
        }
        """
        user = Customer.objects.get(customer_id=request.session['customer_id'])
        boardgame_sort_mode = request.POST.get('boardgame_sort_mode')
        category = request.POST.get('boardgame_filter')
        table_sort_mode = request.POST.get('table_sort_mode')
        capacity = request.POST.get('table_filter')
        
        return render(request, 'app/index.html', 
                    {'boardgame': BoardGame.get_sorted_data(boardgame_sort_mode, category),
                     'table': Table.get_sorted_data(table_sort_mode, capacity),
                     'my_table_book': Booking.objects.filter(customer=user, item_type='Table'),
                     'my_bg_book': Booking.objects.filter(customer=user, item_type='BoardGame'),
                     })
            

    def get_queryset(self):
        """
        Return dict consists of 2 datas: `boardgame`, and `table`.
        
        context_object_name = `data`

        data = {
            boardgame: [`BoardGame.objects`]
            table: [`Table.objects`]
        }
        """
        return {
            'boardgame': BoardGame.objects.all(),
            'table': Table.objects.all()
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

        redirect_url = redirect('board_game_cafe:rent')
        what_do = request.POST['what_do']
        
        def rent():
            item_type = request.POST['item_type']
            item_id = request.POST['item_id']
            user = Customer.objects.get(customer_id=request.session['customer_id'])
            try:
                due_date_str = request.POST['due_date']
                due_date = make_aware(datetime.strptime(due_date_str, "%Y-%m-%d"))
            except ValueError:
                messages.error(request, "Invalid due date format. Please use YYYY-MM-DD.")
                return redirect('board_game_cafe:rent')
            
            Booking.delete_if_exists(item_type, item_id, self.user)

            day_or_hour = 'hours' if item_type == 'Table' else 'days'

            item = {'Table': Table, 'BoardGame': BoardGame}.get(item_type)

            if not Rental.is_good_due_date(due_date, item_type):
                messages.warning(request, f"You can rent {item_type.lower()} {item.max_rent_time} {day_or_hour} at a time.")
                return redirect_url
                
            if not Rental.can_rent(user, item_type):
                messages.warning(request, f"You can rent {item.max_rent} {item_type.lower()} at a time.")
                return redirect_url

            Rental.objects.create(customer=user,
                                    item_type=item_type,
                                    item_id=item_id,
                                    due_date=due_date
                                    )
            if item_type == 'BoardGame':
                BoardGame.objects.get(boardgame_id=item_id).rent_boardgame()
            
            messages.info(request, "Your rental order has been created.")

            return redirect_url


        def sort():
            boardgame_sort_mode = request.POST.get('boardgame_sort_mode')
            category = request.POST.get('boardgame_filter')
            table_sort_mode = request.POST.get('table_sort_mode')
            capacity = request.POST.get('table_filter')

            boardgame_obj = BoardGame.get_sorted_data(boardgame_sort_mode, category)

            table_obj = Table.get_sorted_data(table_sort_mode, capacity)
        
            return render(request, 'app/index.html', 
                    {'boardgame': boardgame_obj,
                     'table': table_obj})

        what_do_handler = {'sort': sort,
                           'rent': rent}
        
        return what_do_handler.get(what_do)()
        
    def get_queryset(self):
        """
        Return dict consists of 2 datas: `boardgame`, and `table`.
        
        context_object_name = `item`

        item = {
            boardgame: [`BoardGame.objects`]
            table: [`Table.objects`]
        }
        """
        renting = Rental.objects.filter(customer=self.user,
                                        status="rented", item_type="BoardGame").values_list('item_id', flat=True)
        not_available = BoardGame.objects.filter(stock=0).values_list('boardgame_id', flat=True)

        return {
            'boardgame': BoardGame.objects.exclude(boardgame_id__in=list(renting)+list(not_available)),
            'table': [table
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
        """
        POST DATA SCHEMA:
        {
            rental_id: str|int
        }
        """
        rental = Rental.objects.get(rental_id=request.POST['rental_id'])
        item_type = rental.item_type
        item_id = rental.item_id
        rental_fee = rental.compute_fee()
        item = rental.get_item()
        if rental.item_type == 'BoardGame':
            item.return_boardgame()
        Booking.update_queue(item_type=item_type, item_id=item_id)
        messages.info(f"There is {rental_fee} Baht fee for your rental.")
        return render(request, self.template_name, self.get_queryset())
        

    def get_queryset(self):
        """
        Return dict consists of 2 datas: `boardgame`, and `table`.
        
        context_object_name = `data`

        data = {
            boardgame: [`BoardGame.objects`]
            table: [`Table.objects`]
        }
        """

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
        week_day = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
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
    