from django.shortcuts import render, redirect
# from django.contrib.auth import login, authenticate
from django.core.exceptions import ValidationError
from .forms import RegisterForm, LoginForm
import random


def home(response):
    return render(response, "main/index.html")#, {"register_form": RegisterForm(), "login_form": LoginForm()})

def rules(response):
    return render(response, "main/index.html")#, {"register_form": RegisterForm(), "login_form": LoginForm()})

def login(response):
    return render(response, "main/index.html")#, {"register_form": RegisterForm(), "login_form": LoginForm()})

def register(response):
    print(response)
    if response.method == "POST":
        print("POST REQUEST")
        if response.POST.get('submit') == 'Register':
            print("REGISTER POST REQUEST")
            form = RegisterForm(response.POST)
            print(form)
            if form.is_valid():
                print("is valid")
                form.instance.username = f'{random.randrange(10000000)}'
                form.save()
                # return redirect(response, "main/")
            else:
                print("AAAA"*100)
                print(form.errors)
                return render(response, "main/index.html", {"register_form": form, "login_form": LoginForm(), "anchor": "registration"})
        elif response.POST.get('submit') == 'Login':
            print("THERE")
        # that's for testing.
        return render(response, "main/index.html", {"register_form": form, "login_form": LoginForm()})
    else:
        return redirect("main/index.html", {"register_form": RegisterForm(), "login_form": LoginForm()})

def profile(response):
    return render(response, "main/index.html")#, {"register_form": RegisterForm(), "login_form": LoginForm()})

def buy(response):
    return render(response, "main/index.html")#, {"register_form": RegisterForm(), "login_form": LoginForm()})
