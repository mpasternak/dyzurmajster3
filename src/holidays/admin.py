from django.contrib import admin
from django.utils.formats import date_format

from holidays.models import Holiday


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ['date', 'dzien_tygodnia']
    def dzien_tygodnia(self, obj):
        return date_format(obj.date, "l")

    pass
