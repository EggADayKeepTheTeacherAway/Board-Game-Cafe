"""Views class for element that show to the user."""

from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.views import generic


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

class PostView(generic.ListView):
    """Class for display the input field for the user when clicking the book button."""
    template_name = "app/post_field.html"

    def get_queryset(self):
        action = self.request.GET.get("action", "default")
        return [{"action": action}]


class RentView(generic.ListView):
    """Class for display rent page."""
    template_name = "app/rent.html"

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

