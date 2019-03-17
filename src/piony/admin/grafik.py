from django.contrib import admin

from piony.models import Grafik, ZestawiajRazem


class ZestawiajRazemInline(admin.TabularInline):
    model = ZestawiajRazem
    extra = 0

@admin.register(Grafik)
class GrafikAdmin(admin.ModelAdmin):
    list_fields = ['uuid', 'nazwa', 'pion_dla_nierozpisanych']
    fields = ['nazwa' ,'uuid', 'pion_dla_nierozpisanych']
    readonly_fields = ['uuid']
    inlines = [ZestawiajRazemInline, ]
