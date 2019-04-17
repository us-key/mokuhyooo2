from django.shortcuts import render
from django.views import generic

from .models import FreeInput

# Create your views here.

def display_index(request):
    ip_addr = request.META.get('REMOTE_ADDR'),
    return render(request, 'objectives/index.html', {'ip_addr':ip_addr})