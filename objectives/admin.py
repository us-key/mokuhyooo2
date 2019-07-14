from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, FreeInput, NumberObjectiveMaster, NumberObjective, NumberObjectiveOutput

class FreeInputAdmin(admin.ModelAdmin):
    list_display = ('year','day_index','input_unit','input_kind','free_word','user')

class NumberObjectiveMasterAdmin(admin.ModelAdmin):
    list_display = ('name','number_kind','summary_kind','valid_flag','user')

class NumberObjectiveAdmin(admin.ModelAdmin):
    list_display = ('master','iso_year','week_index','objective_value')

class NumberObjectiveOutputAdmin(admin.ModelAdmin):
    list_display = ('master','year','month','iso_year','week_index','date_index','day_of_week','output_value')

# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(FreeInput, FreeInputAdmin)
admin.site.register(NumberObjectiveMaster, NumberObjectiveMasterAdmin)
admin.site.register(NumberObjective, NumberObjectiveAdmin)
admin.site.register(NumberObjectiveOutput, NumberObjectiveOutputAdmin)
