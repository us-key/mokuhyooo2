from django.urls import path,include

from . import views

app_name = 'objectives'
urlpatterns = [
    path('', views.display_index, name='index'),
    path('display_date', views.display_date_data, name='display_date'),
    path('master', views.NumberObjectiveMasterListView.as_view(), name='master_list'),
    path('master/create', views.NumberObjectiveMasterCreateView.as_view(), name='master_create'),
    path('week_objective/create/<str:datestr>', views.display_week_objective_form, name='week_objective_create'),

    # ajax
    path('ajax/freeword/register', views.ajax_freeword_register, name='ajax_freeword_register'),
    path('ajax/freeword/get', views.ajax_freeword_get, name='ajax_freeword_get'),
    path('ajax/weekobj/create', views.ajax_weekobj_create, name="ajax_weekobj_create"),
]