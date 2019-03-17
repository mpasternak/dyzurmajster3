from django.contrib import admin

from piony.models import Grafik


@admin.register(Grafik)
class GrafikAdmin(admin.ModelAdmin):
    list_fields = ['uuid', 'nazwa']
    fields = ['nazwa' ,'uuid']
    readonly_fields = ['uuid']
