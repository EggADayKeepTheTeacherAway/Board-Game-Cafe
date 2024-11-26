"""Views class for element that show to the user."""

from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.views import generic
from models import Rental, Table, BoardGame


class LoginView(generic.ListView):
    """Class for login page"""
    template_name = "account.html"

    def get_queryset(self):
        return []


class HomeView(generic.ListView):
    """Class for display Home page."""
    template_name = "app/index.html"

    def get_queryset(self):
        return []


class RentView(generic.ListView):
    """Class for display rent page."""
    model = Rental
    template_name = "app/rent.html"

    context_object_name = ''

    def get_queryset(self):
        return []


class ReturnView(generic.ListView):
    """Class for display return page."""
    template_name = "app/return.html"

    def get_queryset(self):
        return []

