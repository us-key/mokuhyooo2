from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, FreeInput, NumberObjectiveMaster, NumberObjective, NumberObjectiveOutput

# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(FreeInput)
admin.site.register(NumberObjectiveMaster)
admin.site.register(NumberObjective)
admin.site.register(NumberObjectiveOutput)
