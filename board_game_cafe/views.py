"""Views class for element that show to the user."""

from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import F
from django.views import generic
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
                      if table.is_available]
        }


class ReturnView(generic.ListView):
    """Class for display return page."""
    template_name = "app/return.html"

    def get_queryset(self):
        return []


class StatView(generic.ListView):
    """Class for display statistic of many thing."""
    template_name = "app/statistic.html"

    def get_queryset(self):
        return []


class ProfileView(generic.ListView):
    """Class for display the profile of customer."""
    template_name = "app/profile.html"

    def get_queryset(self):
        return []