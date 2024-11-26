"""Urls module for travel to each poll html."""
from django.urls import path

from . import views

app_name = "board_game_cafe"
urlpatterns = [
    path("", views.LoginView.as_view(), name="login"),
    path("book/", views.HomeView.as_view(), name="index"),
    path("rent/", views.RentView.as_view(), name="rent"),
    path("return/", views.ReturnView.as_view(), name="return"),
    path("input/", views.PostView.as_view(), name="post_view"),
    path("stat/", views.StatView.as_view(), name="stat"),
]
