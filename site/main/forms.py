from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django import forms


class RegisterForm(UserCreationForm):
    # email = forms.CharField(widget=forms.TextInput(attrs=dict(type="email", placeholder="E-mail", name="r-email")))
    email = forms.EmailField()
    # password = forms.CharField(widget=forms.TextInput(attrs=dict(type="password", placeholder="Password", name="r-password")))
    # password2 = forms.CharField(widget=forms.TextInput(attrs=dict(type="password", placeholder="Password", name="r-password-repeat")))
    # email = forms.CharField()
    # password = forms.CharField()
    # password2 = forms.CharField()

    def clean(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email exists")
        return self.cleaned_data

    class Meta:
        model = User
        fields = ["email", "password1", "password2"]

class LoginForm(UserCreationForm):
    email = forms.CharField(widget=forms.TextInput(attrs=dict(type="email", placeholder="E-mail", name="r-email")))
    password = forms.CharField(widget=forms.TextInput(attrs=dict(type="password", placeholder="Password", name="r-password")))
    class Meta:
        model = User
        fields = ["email", "password"]
