from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm


def index(response):
    return render(response, "main/index.html", {})

def register(response):
    print(response)
    if response.method == "POST":
        if response.POST.get('submit') == 'Register':
            print("HERE")
            # your sign in logic goes here
        elif response.POST.get('submit') == 'Enter':
            print("THERE")
            # your sign up logic goes here
        form = UserCreationForm()
        if form.is_valid():
            form.save()
            return redirect("/")
    else:
        form = UserCreationForm()

    return render(response, "main/index.html", {"register_form":form})
