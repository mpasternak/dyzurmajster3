from django import forms


class ParametryWydrukuForm(forms.Form):
    start = forms.DateField(required=False)
    koniec = forms.DateField(required=False)
