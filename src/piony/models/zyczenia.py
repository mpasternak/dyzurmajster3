# -*- encoding: utf-8 -*-
from datetime import date

from dateutil import relativedelta
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from mptt.fields import TreeForeignKey, TreeManyToManyField

from piony import const
from piony.models.util import lista_dni, sprawdz_liste_wobec_miesiaca, parsuj_liste_dni
from .pion import Pion


class BazaZyczen(models.Model):
    parent = models.ForeignKey("piony.ZyczeniaPracownika", models.CASCADE)

    pion = TreeForeignKey(Pion, models.CASCADE, blank=True, null=True, related_name="+")

    adnotacja = models.CharField(max_length=50, blank=True, null=True)

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
            if self.rodzaj_pionu != self.pion.rodzaj_pionu:
                raise ValidationError({
                    "rodzaj_pionu": "Wybrano różny rodzaj pionu i pion, reguła nie będzie miała sensu"
                })


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

    def clean(self):
        super(ZyczeniaSzczegolowe, self).clean()

        sprawdz_liste_wobec_miesiaca(
            self.lista_dni,
            self.miesiac_i_rok
        )

    class Meta:
        verbose_name = 'życzenie szczegółówe'
        verbose_name_plural = 'życzenia szczegółowe'


class ZyczeniaOgolne(BazaZyczen):
    start = models.DateField("Początek", blank=True, null=True)
    koniec = models.DateField("Koniec", blank=True, null=True)

    dzien_1 = models.BooleanField("Pon.", default=True)
    dzien_2 = models.BooleanField("Wt.", default=True)
    dzien_3 = models.BooleanField("Śr.", default=True)
    dzien_4 = models.BooleanField("Czw.", default=True)
    dzien_5 = models.BooleanField("Pt.", default=True)
    dzien_6 = models.BooleanField("Sob.", default=True)
    dzien_7 = models.BooleanField("Nie.", default=True)

    dostepny = models.BooleanField("Dostępny/a", default=True)

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


class ZyczeniaPracownika(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

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
    maks_dniowki_w_tygodniu = models.PositiveSmallIntegerField("Maks. dniówek w tygodniu", default=None, blank=True, null=True)
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

    def wszystkie_dozwolone_piony(self):
        s = set()
        for pion in self.dozwolone_piony.all():
            s.add(pion)
            for pion in pion.get_descendants():
                s.add(pion)
        return s
