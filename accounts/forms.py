from django.contrib.auth.forms import UserCreationForm as UForm
from django.contrib.auth.forms import UsernameField as UField
from django.contrib.auth import (
    authenticate, get_user_model, password_validation,
)

class UserCreationForm(UForm):

    class Meta:
        model = get_user_model()
        fields = ("username",)
        field_classes = {'username': UField}
