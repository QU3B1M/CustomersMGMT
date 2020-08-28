from django.shortcuts import render
from django.http import HttpResponse


def home(request):
    return render(request, 'app/dashboard.html')

def products(request):
    return render(request, 'app/products.html')

def customer(request):
    return render(request, 'app/customer.html')
