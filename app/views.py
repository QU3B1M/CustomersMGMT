from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import *
from .forms import OrderForm


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


def customer(request, pk):
    customer = Customer.objects.get(id=pk)
    orders = customer.order_set.all()
    orders_count = orders.count()

    context = {
        'customer':customer,
        'orders':orders,
        'orders_count':orders_count
    }

    return render(request, 'app/customer.html', context)


def create_order(request):
    form = OrderForm()
    
    if request.method == 'POST':
        form = OrderForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('/')
    
    context = {
        
        
        'form': form
        }
    
    return render(request, 'app/order_form.html', context)


def update_order(request, pk):
    
    order = Order.objects.get(id=pk)
    form = OrderForm(instance=order)
    
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)

        if form.is_valid():
            form.save()
            return redirect('/')
    
    context = {
        'form': form
        }
    
    return render(request, 'app/order_form.html', context)


def delete_order(request, pk):
    
    order = Order.objects.get(id=pk)
    # form = OrderForm(instance=order)
    
    if request.method == 'POST':
        order.delete()
        # form = OrderForm(request.POST, instance=order)

        # if form.is_valid():
        #     form.save()
        return redirect('/')
    
    context = {
        'item': order
        }
    
    return render(request, 'app/delete.html', context)


