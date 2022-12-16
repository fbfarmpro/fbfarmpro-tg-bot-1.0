from django.contrib.auth.forms import UserCreationForm
from django import forms

class User(UserCreationForm):
    # email = forms.CharField(widget=forms.EmailInput)
    # password = forms.CharField(widget=forms.PasswordInput)
    email = forms.CharField()
    password = forms.CharField()
