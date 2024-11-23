"""Urls module for travel to each poll html."""
from django.urls import path

from . import views

app_name = "board_game_cafe"
urlpatterns = [
    path("", views.HomeView.as_view(), name="index"),
]
