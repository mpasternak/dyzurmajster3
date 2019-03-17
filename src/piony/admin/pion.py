from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from piony.models import Pion, PrzerwaWPracyPionu


class PrzerwaWPracyPionuInline(admin.TabularInline):
    model = PrzerwaWPracyPionu
    extra = 0

@admin.register(Pion)
class PionAdmin(MPTTModelAdmin):
    inlines = [PrzerwaWPracyPionuInline]
    list_filter = ['rodzaj', 'priorytet']
    list_display = ['nazwa', 'rodzaj', 'priorytet', 'sort']
    pass
