from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.forms import inlineformset_factory
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .models import *
from .forms import OrderForm, CreateUserForm
from .filters import OrderFilter


@login_required(login_url='login')
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


def signup_login(request):
    if request.user.is_authenticated:
        return redirect('home')     
    else:
        form = CreateUserForm()        
        if request.method == "POST":  
             
            if request.POST.get('submit') == 'sign_up':            
                form = CreateUserForm(request.POST)   
                if form.is_valid():
                    form.save()
                    user = form.cleaned_data.get('username')
                    messages.success(request, 'User {} was created successfully'.format(user))
                else: 
                    messages.error(request, 'Nope')
                    
            elif request.POST.get('submit') == 'sign_in':
                username = request.POST.get('username')
                password = request.POST.get('password')
                user = authenticate(request, username=username, password=password)                    
                if user is not None:
                    login(request, user)
                    return redirect('home')
                else:
                    messages.info(request, 'Username or Password is Incorrect')
                
        context = {
            'form': form
        }
        
        return render(request, 'app/login.html', context)


@login_required(login_url='login')
def logout_user(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def products(request):
    products = Product.objects.all()
    
    return render(request, 'app/products.html', {'products': products})


@login_required(login_url='login')
def customer(request, pk):
    customer = Customer.objects.get(id=pk)
    orders = customer.order_set.all()
    orders_count = orders.count()
    my_filter = OrderFilter(request.GET, queryset=orders)
    orders = my_filter.qs

    context = {
        'customer':customer,
        'orders':orders,
        'orders_count':orders_count,
        'my_filter': my_filter
    }

    return render(request, 'app/customer.html', context)


@login_required(login_url='login')
def create_order(request, pk):
    OrderFormSet = inlineformset_factory(Customer, Order, fields=('product', 'status'), extra=1, can_delete=False)
    customer = Customer.objects.get(id=pk)
    formset = OrderFormSet(queryset=Order.objects.none(), instance=customer)
    
    if request.method == 'GET':
        formset = OrderFormSet(request.GET or None)
    elif request.method == 'POST':
        formset = OrderFormSet(request.POST, instance=customer)

        if formset.is_valid():
            formset.save()
            return redirect('customer', pk=pk)
    
    context = {
        'formset': formset
        }
    
    return render(request, 'app/order_form.html', context)


@login_required(login_url='login')
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
    
    return render(request, 'app/update_order_form.html', context)


@login_required(login_url='login')
def delete_order(request, pk):    
    order = Order.objects.get(id=pk)
    
    if request.method == 'POST':
        order.delete()
        return redirect('/')
    
    context = {
        'item': order
        }
    
    return render(request, 'app/delete.html', context)
