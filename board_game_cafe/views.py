"""Views class for element that show to the user."""

from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.contrib import messages
from django.views import generic
from .forms import RegisterForm, LoginForm
from .models import (Rental, Table, BoardGame,
                     Customer, BoardGameCategory,
                     BoardGameGroup)


def login(request):
    form = LoginForm()
    if request.method == "POST":
        customer_name = request.POST['customer_name']
        password = request.POST['password']
        user = Customer.objects.filter(customer_name=customer_name, password=password)
        if user.exists():
            user = user.get()
            request.session['customer_id'] = user.customer_id 
            return redirect('board_game_cafe:index')
        messages.error(request,
                       "You entered wrong username or password, or you forgot to sign up.")
    return render(request, 'login.html', {'form': form})


def signup(request):
    form = RegisterForm()
    if request.method == "POST":
        customer_name = request.POST['customer_name']
        password = request.POST['password']
        contact = request.POST['contact']
        if Customer.objects.filter(customer_name=customer_name,
                                       password=password,
                                       contact=contact).exists():
            messages.warning(request, "You already have an account.")
            return redirect('login')
        user = Customer.objects.create(customer_name=customer_name,
                                    password=password,
                                    contact=contact)
        request.session['customer_id'] = user.customer_id
        return redirect('board_game_cafe:index')
    return render(request, 'signup.html', {'form': form})


class HomeView(generic.ListView):
    """Class for display Home page."""
    template_name = "app/index.html"

    def get_queryset(self):
        return []


class PostView(generic.ListView):
    """Class for display the input field for the user when clicking the book button."""
    template_name = "app/post_field.html"

    def get_queryset(self):
        action = self.request.GET.get("action", "default")
        return [{"action": action}]


class RentView(generic.ListView):
    """Class for display rent page."""
    model = Rental
    template_name = "app/rent.html"

    context_object_name = 'item'

    def get_queryset(self):

        return []


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