from adminsortable2.admin import SortableInlineAdminMixin
from django.contrib import admin

from piony.models.wydruk import ElementWydruku, Wydruk


class ElementWydrukuInline(SortableInlineAdminMixin, admin.TabularInline):
    extra = 0
    model = ElementWydruku


@admin.register(Wydruk)
class WydrukAdmin(admin.ModelAdmin):
    inlines = [ElementWydrukuInline, ]
    fields = ['kod', 'nazwa', 'rodzaj']
    list_display = ['kod', 'nazwa', 'rodzaj']
