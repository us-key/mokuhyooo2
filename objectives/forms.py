from django import forms
from .models import NumberObjectiveMaster


class NumberObjectiveMasterForm(forms.ModelForm):
    '''数値目標マスターフォーム'''
    class Meta:
        model = NumberObjectiveMaster
        fields = ('name', 'number_kind', 'summary_kind',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
