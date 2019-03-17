from django import forms
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.models import User


class DyzurmajsterUserChoiceField(forms.ModelChoiceField):
    def __init__(self, *args, **kw):
        super(DyzurmajsterUserChoiceField, self).__init__(
            User.objects.all().order_by('last_name', 'first_name'),
            *args, **kw
        )

    def label_from_instance(self, obj):
        return f"{obj.last_name} {obj.first_name}"


class DyzurmajsterUserFilter(SimpleListFilter):
    title = "Pracownik"
    parameter_name = 'pracownik'

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        users = dict(
            [(x.pk, f"{x.last_name} {x.first_name}") for x in User.objects.all()]
        )
        return [(i['user'], users[i['user']]) for i in qs.values("user").distinct().order_by("user__last_name")]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user__pk=self.value())
