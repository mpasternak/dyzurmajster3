from adminsortable2.admin import SortableInlineAdminMixin
from django import forms
from django.contrib import admin

from core.admin_helpers import DyzurmajsterUserChoiceField, DyzurmajsterUserFilter
from piony.models import ZyczeniaOgolne, ZyczeniaPracownika, ZyczeniaSzczegolowe, \
    Urlop, Priorytet


# class ZyczeniaOgolneForm(forms.ModelForm):
#     def __init__(self, *args, **kw):
#         super(ZyczeniaOgolneForm, self).__init__(*args, **kw)
#         import pytest; pytest.set_trace()


class OgraniczPionyMixin:
    """Ogranicz piony do wyboru do tych ktore uzytkownik ma dozwolone
    oraz do ich wszystkich pionow podrzednych.
    """

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super(OgraniczPionyMixin, self).formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == 'pion':
            obj = request.__zyczenia_pracownika__
            if obj is not None:
                field.queryset = field.queryset.filter(
                    pk__in=[pion.pk for pion in obj.wszystkie_dozwolone_piony()])
            else:
                field.queryset = field.queryset.none()

        return field


class ZyczeniaOgolneInline(SortableInlineAdminMixin, OgraniczPionyMixin, admin.TabularInline):
    model = ZyczeniaOgolne
    fields = ['adnotacja', 'start', 'koniec', 'rodzaj_pionu', 'pion',
              'dostepny', 'tylko_dni_powszednie',
              'dzien_1', 'dzien_2', 'dzien_3', 'dzien_4', 'dzien_5',
              'dzien_6', 'dzien_7', 'ilosc_zastosowan']
    extra = 0


class ZyczeniaSzczegoloweInline(OgraniczPionyMixin, admin.TabularInline):
    model = ZyczeniaSzczegolowe
    fields = ['miesiac_i_rok', 'rodzaj_pionu', 'lista_dni', 'adnotacja', 'pion']
    extra = 0


class UrlopInline(admin.TabularInline):
    model = Urlop
    fields = ['rodzaj', 'start', 'koniec']
    extra = 0


class PriorytetInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Priorytet
    fields = ['start', 'koniec', 'piony', 'priorytet']
    extra = 0


class ZyczeniaPracownikaForm(forms.ModelForm):
    user = DyzurmajsterUserChoiceField()

    def __init__(self, *args, **kwargs):
        super(ZyczeniaPracownikaForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.id:
            self.fields['user'].disabled = True

    class Meta:
        fields = ["user"]

        widgets = {
            "piony": forms.SelectMultiple(attrs={'size': '30', 'style': 'height: unset;'})
        }
        model = ZyczeniaPracownika


@admin.register(ZyczeniaPracownika)
class ZyczeniaPracownikaAdmin(admin.ModelAdmin):
    filter_horizontal = ['dozwolone_piony', ]
    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        ('DOZWOLONE PIONY', {
            'classes': ('collapse',),
            'fields': (
                'dozwolone_piony',
            )
        }),
        ('OPCJE', {
            'classes': ('collapse',),
            'fields': (
                'adnotacje',
                'dniowka_co_ile_dni',
                'dyzur_co_ile_dni',
                'maks_godzin_ciaglej_pracy',
                'min_odpoczynek_po_ciaglej_pracy',
                'priorytet_bazowy',
                'maks_dyzury',
                'maks_dobowe',
                'maks_zwykle',
                'maks_dniowki',
                'maks_dniowki_w_tygodniu',
                'nie_dyzuruje_z',
                'specjalizacja',
                'emeryt'
            ),
        }),
    )
    form = ZyczeniaPracownikaForm
    list_display = ['last_name', 'first_name', 'priorytet_bazowy', 'specjalizacja', 'emeryt']
    inlines = [UrlopInline, PriorytetInline, ZyczeniaOgolneInline, ZyczeniaSzczegoloweInline]
    list_filter = [DyzurmajsterUserFilter, 'specjalizacja', 'emeryt']
    search_fields = ['user__username', 'user__last_name']
    ordering = ['user__last_name']
    list_select_related = True

    def last_name(self, obj):
        return obj.user.last_name

    last_name.short_description = "Nazwisko"

    def first_name(self, obj):
        return obj.user.first_name

    first_name.short_description = "Imię"

    def get_form(self, request, obj=None, **kwargs):
        # just save obj reference for future processing in Inline
        request.__zyczenia_pracownika__ = obj
        return super(ZyczeniaPracownikaAdmin, self).get_form(request, obj, **kwargs)
