from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from piony.models import Pion, PrzerwaWPracyPionu, DostepnoscOgolnaPionu, PionNiePracuje  # , KolejnoscPracownikaWPionie


class PrzerwaWPracyPionuInline(admin.TabularInline):
    model = PrzerwaWPracyPionu
    extra = 0


class DostepnoscOgolnaPionuInline(admin.TabularInline):
    model = DostepnoscOgolnaPionu
    extra = 0

    fields = ['adnotacja', 'start', 'koniec',
              'dostepny', 'tylko_dni_powszednie',
              'dzien_1', 'dzien_2', 'dzien_3', 'dzien_4', 'dzien_5',
              'dzien_6', 'dzien_7', ]


# class KolejnoscPracownikaWPionieInline(SortableInlineAdminMixin, admin.TabularInline):
#     model = KolejnoscPracownikaWPionie
#     extra = 0

@admin.register(Pion)
class PionAdmin(MPTTModelAdmin):
    inlines = [PrzerwaWPracyPionuInline, DostepnoscOgolnaPionuInline]  # KolejnoscPracownikaWPionieInline]
    list_filter = ['rodzaj', 'priorytet']
    list_display = ['nazwa', 'rodzaj', 'symbol', 'domyslnie_dostepny', 'priorytet', 'sort']
    pass


@admin.register(PionNiePracuje)
class PionNiePracujeAdmin(admin.ModelAdmin):
    pass
