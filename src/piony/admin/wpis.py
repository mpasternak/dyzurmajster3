from django.contrib import admin
from django.utils.formats import date_format
from mptt.admin import TreeRelatedFieldListFilter

from piony.models import Wpis, Wolne


@admin.register(Wpis)
class WpisAdmin(admin.ModelAdmin):
    search_fields = ['pion__nazwa', 'pion__rodzaj', 'user__username', 'user__last_name', 'dzien']
    list_filter = [('pion', TreeRelatedFieldListFilter),
                   'pion__rodzaj',
                   'user']

    list_display = ['dzien', 'dzien_tygodnia', 'pion', 'user']

    ordering = ('dzien', 'pion')

    def dzien_tygodnia(self, obj):
        return date_format(obj.dzien, "l")


@admin.register(Wolne)
class WolneAdmin(admin.ModelAdmin):
    list_display = ['dzien', 'user', 'przyczyna']
    list_filter = ['user']
    pass
