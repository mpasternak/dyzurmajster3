# -*- encoding: utf-8 -*-

from dateutil import relativedelta
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models import Q
from mptt.fields import TreeForeignKey, TreeManyToManyField

from piony import const
from piony.models.util import lista_dni, sprawdz_liste_wobec_miesiaca, parsuj_liste_dni, DostepnoscOgolnaMixin, \
    ModelZAdnotacjaMixin
from .pion import Pion


class BazaZyczen(ModelZAdnotacjaMixin, models.Model):
    parent = models.ForeignKey("piony.ZyczeniaPracownika", models.CASCADE)

    pion = TreeForeignKey(Pion, models.CASCADE, blank=True, null=True, related_name="+")

    rodzaj_pionu = models.PositiveSmallIntegerField(
        choices=(
            (None, "każdy"),
            (const.DZIENNY, "dzienny"),
            (const.NOCNYSWIATECZNY, "nocny/świąteczny")
        ),
        blank=True,
        null=True,
    )

    def clean(self):
        # Sprawdź, czy wybrany pion jest jednym z pionów dozwolonych dla użytkownika

        if self.pion is None:
            return

        pks = [pion.pk for pion in self.parent.wszystkie_dozwolone_piony()]
        if self.pion.pk not in pks:
            raise ValidationError({
                "pion": "Wybrany pion nie jest w dozwolonych pionach dla tego użytkownika."
            })

        if self.rodzaj_pionu and self.pion:
            if self.pion.rodzaj is not None and self.rodzaj_pionu != self.pion.rodzaj:
                raise ValidationError({
                    "rodzaj_pionu": "Wybrano różny rodzaj pionu i pion, reguła nie będzie miała sensu"
                })

    def relevant(self, pion, dzien):
        if self.pion is not None:
            # Ta reguła ma podany pion. Zasadą jest, że akceptujemy wszystkie pod-piony
            # pionu podanego jako nadrzędny w regule:
            if pion not in self.pion.get_descendants(include_self=True):
                return False

        if self.rodzaj_pionu is not None:
            if self.rodzaj_pionu != pion.rodzaj:
                return False

        return self.relevant_zakres_dat(dzien)

    class Meta:
        abstract = True


def next_month():
    from django.utils import timezone
    return (timezone.now().date() + relativedelta.relativedelta(months=1)).replace(day=1)


class ZyczeniaSzczegolowe(BazaZyczen):
    miesiac_i_rok = models.DateField(default=next_month)

    lista_dni = models.CharField(
        max_length=200,
        validators=[lista_dni])

    def dni(self):
        return parsuj_liste_dni(self.lista_dni)

    def daty(self):
        for elem in self.dni():
            yield self.miesiac_i_rok.replace(day=elem)

    def clean(self):
        super(ZyczeniaSzczegolowe, self).clean()

        sprawdz_liste_wobec_miesiaca(
            self.lista_dni,
            self.miesiac_i_rok
        )

        # TODO: sprawdź, czy nie ma nachodzących na siebie okresów zdefiniowanych w bazie

    def relevant_zakres_dat(self, dzien):
        return dzien in self.daty()

    def czy_dostepny(self, dzien):
        if dzien in self.daty():
            return True
        return False

    class Meta:
        verbose_name = 'życzenie szczegółówe'
        verbose_name_plural = 'życzenia szczegółowe'

    def __str__(self):
        ret = f"Życzenie szczegółowe dla {self.parent.user} na miesiąc {self.miesiac_i_rok}, {self.lista_dni}"
        if self.pion:
            ret += f" pion {self.pion}"
        if self.rodzaj_pionu:
            ret += f" rodzaj {self.rodzaj_pionu}"
        return ret


class ZyczeniaOgolne(DostepnoscOgolnaMixin, BazaZyczen):
    ilosc_zastosowan = models.PositiveSmallIntegerField(
        "Ilość zastosowań",
        null=True,
        blank=True,
        default=None,
        help_text="Ile razy ta reguła ma być spełniona podczas trwania jej czasokresu. Czyli np. "
                  "'maksymalnie 2 dyżury od 1go do 15go'. ")

    def __str__(self):
        return f"Życzenie {self.adnotacja} dla {self.parent.user}"

    class Meta:
        verbose_name_plural = 'życzenia ogólne'
        verbose_name = 'życzenie ogólne'
        ordering = ['kolejnosc']


class ZyczeniaPracownika(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    adnotacje = models.TextField(null=True, blank=True)

    dozwolone_piony = TreeManyToManyField(Pion, related_name="+")

    dniowka_co_ile_dni = models.PositiveIntegerField(
        "Jest w stanie wziąć dniówkę co tyle dni od ostatniej",
        default=1
    )

    dyzur_co_ile_dni = models.PositiveIntegerField(
        "Jest w stanie wziąć dyżur co tyle dni od ostatniego ciągu pracy",
        default=2,
    )

    maks_godzin_ciaglej_pracy = models.PositiveIntegerField(
        "Maksymalna ilość godzin ciągłej pracy",
        default=24,
    )

    min_odpoczynek_po_ciaglej_pracy = models.PositiveIntegerField(
        "Czas bez pracy po godzinach ciągłej pracy",
        default=11,
        validators=[
            MaxValueValidator(24)
        ]
    )

    priorytet_bazowy = models.PositiveSmallIntegerField(default=50)

    maks_dniowki = models.PositiveSmallIntegerField("Maks. dniówek", default=None, blank=True, null=True)
    maks_dniowki_w_tygodniu = models.PositiveSmallIntegerField("Maks. dniówek w tygodniu", default=None, blank=True,
                                                               null=True)
    maks_dyzury = models.PositiveSmallIntegerField("Maks. dyżurów", default=None, blank=True, null=True)
    maks_dobowe = models.PositiveSmallIntegerField("Maks. dobowych", default=None, blank=True, null=True)
    maks_zwykle = models.PositiveSmallIntegerField("Maks. zwykłych", default=None, blank=True, null=True)

    nie_dyzuruje_z = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="+", blank=True)

    specjalizacja = models.SmallIntegerField(
        null=True,
        default=None,
        choices=(
            (None, "żaden"),
            (const.REZYDENT, "rezydent"),
            (const.JEDYNKOWICZ, "jedynkowicz"),
            (const.SPECJALISTA, "specjalista")
        ),
    )

    emeryt = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'życzenia pracowników'
        verbose_name = 'życzenia pracownika'

    def __str__(self):
        ret = f"Życzenia dla {self.user}"

        if self.maks_dobowe is not None:
            ret += f" - weźmie {self.maks_dobowe} dobowych dyżurów"

        if self.maks_zwykle is not None:
            ret += f" - weźmie {self.maks_zwykle} zwykłych dyżurów"

        return ret

    # @cached_property
    def wszystkie_dozwolone_piony(self):
        s = set()
        for pion in self.dozwolone_piony.all():
            s.add(pion)
            for pion in pion.get_descendants():
                s.add(pion)
        return s

    def priorytet_pionu(self, dzien, pion):

        for priorytet in self.priorytet_set.filter(
                Q(start__range=(dzien, dzien)) |
                Q(koniec__range=(dzien, dzien)) |
                Q(start__lt=dzien, koniec__gt=dzien)
        ).order_by('kolejnosc'):

            # Znalazł się jeden wpis dla takiego zakresu dat;
            # Czy poszukiwany pion wchodzi w jego skład?
            for elem in [pion.get_descendants(include_self=True) for pion in priorytet.piony.all()]:
                if pion in elem:
                    return priorytet.priorytet

            # Nie wchodzi. Zwróć bazowy priorytet, powiększony o priorytet
            # tego pionu, aby w innych pionach w których brakuje priorytetyzacji
            # opóźnić użytkownika w stosunku do priorytetu bazowego
            return self.priorytet_bazowy + (100 - priorytet.priorytet)

        # Brak priorytetów. Zwróć bazowy priorytet
        return self.priorytet_bazowy

    def czy_ma_urlop(self, dzien):
        return self.urlop_set.filter(
            Q(start__range=(dzien, dzien)) |
            Q(koniec__range=(dzien, dzien)) |
            Q(start__lt=dzien, koniec__gt=dzien)
        ).exists()

    def czy_ma_regule_pozwalajaca_wziac(self, pion, dzien):
        # Sprawdza, czy ten użytkownik może wstepnie wziąć dany pion
        # w dany dzień; bez sprawdzania czasu pracy, godzin itp,
        # bez dotykania obiektu 'Grafik'

        # Ten użytkownik może wziąć coś tego dnia, sprawdźmy, czy ten pion:
        if pion not in self.wszystkie_dozwolone_piony():
            # Ten użytkownik nie ma przypisania do tego pionu
            return False, const.BRAK_PRZYPISANIA, pion

        dopasowanie = False
        for zyczenie in self.zyczeniaszczegolowe_set.all():
            if zyczenie.relevant(pion, dzien):
                dopasowanie = True
                break

        if not dopasowanie:
            for zyczenie in self.zyczeniaogolne_set.all().order_by("-kolejnosc"):
                if zyczenie.relevant(pion, dzien):
                    dopasowanie = True
                    break

        if not dopasowanie:
            return False, const.NIEDOPASOWANE, None

        # Jeżeli mamy adekwatne do pionu/daty życzenie, to wywołajmy
        # mu funkcję czy_dostepny, żeby zobaczyć własnie toL
        dostepny = zyczenie.czy_dostepny(dzien)
        if not dostepny:
            return False, const.ZYCZENIE, zyczenie

        return True, const.ZYCZENIE, zyczenie
