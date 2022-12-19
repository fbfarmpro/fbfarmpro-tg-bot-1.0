from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="first"),
    path("home/", views.home, name="first"),
    path("rules/", views.rules, name="second"),
    path("login/", views.login, name="third"),
    path("register/", views.register, name="fourth"),
    path("profile/", views.profile, name="fiveth"),
    path("buy/", views.buy, name="buy"),
]
