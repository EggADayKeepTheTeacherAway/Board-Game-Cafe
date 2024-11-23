"""Views class for element that show to the user."""

from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.views import generic


class HomeView(generic.ListView):
    """Class for display Home page."""
    template_name = "app/index.html"

    def get_queryset(self):

        return []
