from django.urls import path,include

from . import views

app_name = 'objectives'
urlpatterns = [
    path('', views.display_index, name='index'),
    path('display_date/<str:display_date>', views.display_date_data, name='display_date'),

    # ajax
    path('ajax/freeword/register/', views.ajax_freeword_register),
]