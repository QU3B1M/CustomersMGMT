from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.forms import inlineformset_factory
from .models import *
from .forms import OrderForm
from .filters import OrderFilter


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
    my_filter = OrderFilter(request.GET, queryset=orders)
    orders = my_filter.qs

    context = {
        'customer':customer,
        'orders':orders,
        'orders_count':orders_count,
        'my_filter': my_filter
    }

    return render(request, 'app/customer.html', context)


def create_order(request, pk):
    OrderFormSet = inlineformset_factory(Customer, Order, fields=('product', 'status'), extra=1, can_delete=False)
    customer = Customer.objects.get(id=pk)
    formset = OrderFormSet(queryset=Order.objects.none(), instance=customer)
    
    if request.method == 'GET':
        formset = OrderFormSet(request.GET or None)
    elif request.method == 'POST':
        formset = OrderFormSet(request.POST, instance=customer)

        if formset.is_valid():
            # for form in formset:
            #     product = form.cleaned_data.get('product')
            #     status = form.cleaned_data.get('status')
            #     Order(product=product, status=status, customer=customer).save()
            formset.save()
            return redirect('customer', pk=pk)
    
    context = {
        'formset': formset
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
    
    return render(request, 'app/update_order_form.html', context)


def delete_order(request, pk):
    
    order = Order.objects.get(id=pk)
    
    if request.method == 'POST':
        order.delete()
        return redirect('/')
    
    context = {
        'item': order
        }
    
    return render(request, 'app/delete.html', context)


