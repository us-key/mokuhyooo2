from django.urls import path,include

from . import views

app_name = 'objectives'
urlpatterns = [
    path('', views.display_index, name='index'),
    path('display_date', views.display_date_data, name='display_date'),
    path('master', views.NumberObjectiveMasterListView.as_view(), name='master_list'),
    path('master/create', views.NumberObjectiveMasterCreateView.as_view(), name='master_create'),

    # ajax
    path('ajax/freeword/register', views.ajax_freeword_register),
    path('ajax/freeword/get', views.ajax_freeword_get),
]