from django.shortcuts import render
from django.http import HttpResponse
from .models import *


def home(request):
    orders = Order.objects.all()
    customers = Customer.objects.all()

    total_customers = customers.count()
    total_orders = orders.count()

    done = orders.filter(status='Done').count()
    pending = orders.filter(status='Pending').count()

    context = {
        'orders':orders, 
        'customers':customers, 
        'total_customers':total_customers,
        'total_orders':total_orders,
        'done':done,
        'pending':pending
    }

    return render(request, 'app/dashboard.html', context)

def products(request):
    products = Product.objects.all()
    return render(request, 'app/products.html', {'products': products})

def customer(request):
    return render(request, 'app/customer.html')
