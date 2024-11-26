"""Urls module for travel to each poll html."""
from django.urls import path
from django.views.generic.base import RedirectView

from . import views

app_name = "board_game_cafe"

urlpatterns = [
    path("", views.HomeView.as_view(), name="index"),
    path("rent/", views.RentView.as_view(), name="rent"),
    path("return/", views.ReturnView.as_view(), name="return"),
    path("stat/", views.StatView.as_view(), name="stat"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
]
