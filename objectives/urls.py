from django.urls import path,include

from . import views

app_name = 'objectives'
urlpatterns = [
    path('', views.display_index, name='index'),
]