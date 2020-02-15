from adminsortable.admin import SortableTabularInline, SortableAdmin
from django.contrib import admin

from piony.models.wydruk import ElementWydruku, Wydruk


class ElementWydrukuInline(SortableTabularInline):
    extra = 0
    model = ElementWydruku


@admin.register(Wydruk)
class WydrukAdmin(SortableAdmin):
    inlines = [ElementWydrukuInline, ]
    fields = ['kod', 'nazwa', 'rodzaj', "font_size"]
    list_display = ['kod', 'nazwa', 'rodzaj']
