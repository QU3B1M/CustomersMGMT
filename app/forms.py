from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Order, Customer


class OrderForm(ModelForm):
    
    class Meta:
        model = Order
        fields = '__all__'
        
        
class CustomerForm(ModelForm):
    
    class Meta:
        model = Customer
        fields = '__all__'
        

class CreateUserForm(UserCreationForm):
    username = forms.CharField(label='username',required=True, widget=forms.TextInput(attrs={'placeholder':'Username'}))
    email = forms.EmailField(label = 'email', required=True, widget=forms.TextInput(attrs={'placeholder':'Email'}))
    password1 = forms.CharField(label='password',required=True, widget=forms.PasswordInput(attrs={'placeholder':'Password'}))
    password2 = forms.CharField(label='password',required=True, widget=forms.PasswordInput(attrs={'placeholder':'Password Confirmation'}))
    

    class Meta:
        model = User
        fields = [
            'username', 
            'email', 
            'password1', 
            'password2'
        ]

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with tha email already exists")
        return email
