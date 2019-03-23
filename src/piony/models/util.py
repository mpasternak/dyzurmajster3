from django.core.exceptions import ValidationError
from django.db import models

from holidays.models import Holiday
from piony import const


def lista_dni(value):
    def sprawdz_dzien(v):
        v = v.strip()

        try:
            v = int(v)
        except (ValueError, TypeError):
            raise ValidationError("Podaj listę liczb oddzieloną przecinkami lub zakresy, np. 1,2,3,4-10,12")

        if v < 1:
            raise ValidationError("liczby muszą być dodatnie, większe od zera, a tu jedna z nich to %s" % v)
        if v > 31:
            raise ValidationError("liczby muszą być mniejsze od 31, a tu jedna z nich to %s" % v)

    for elem in value.strip().split(","):
        if elem.find("-") > 0:
            for value in elem.split("-", 1):
                sprawdz_dzien(value)
            continue
        sprawdz_dzien(elem)


def parsuj_liste_dni(v):
    v = v.strip()
    if not v:
        return

    for elem in v.split(","):
        elem = elem.strip()
        if not elem:
            raise ValidationError("Lista zawiera puste elementy. Poszukaj podwójnego przecinka.")

        if elem.find("-") > 0:
            v1, v2 = elem.split("-", 1)
            yield range(int(v1), int(v2) + 1)
            continue
        yield int(elem)


def sprawdz_liste_wobec_miesiaca(lista_dni, baza):
    for elem in parsuj_liste_dni(lista_dni):
        try:
            try:
                baza.replace(day=elem)
            except TypeError:
                for v in elem:
                    baza.replace(day=v)
        except ValueError:
            raise ValidationError("Dla wybranego miesiąca i roku, dzień %s nie jest prawidłowy" % elem)


def spacja_inicjal_z_kropka(s):
    try:
        return " " + s[0].upper() + "."
    except IndexError:
        return ""


def repr_user(user):
    if not user.last_name:
        return user.username
    return f"{user.last_name}{spacja_inicjal_z_kropka(user.first_name)}"


def pracownik_etatowy(pracownik, pion=None, dzien_1=True, dzien_2=True, dzien_3=True, dzien_4=True,
                      dzien_5=True, dzien_6=False, dzien_7=False,
                      specjalizacja=const.SPECJALISTA, **kw):
    from .zyczenia import ZyczeniaPracownika
    dp = ZyczeniaPracownika.objects.create(
        user=pracownik,
        specjalizacja=specjalizacja,
        **kw
    )
    if pion is not None:
        dp.dozwolone_piony.add(pion)

    z = dp.zyczeniaogolne_set.create(
        adnotacja="Etat",
        pion=pion,
        rodzaj_pionu=const.DZIENNY,
        dostepny=True,
        dzien_1=dzien_1,
        dzien_2=dzien_2,
        dzien_3=dzien_3,
        dzien_4=dzien_4,
        dzien_5=dzien_5,
        dzien_6=dzien_6,
        dzien_7=dzien_7,
    )

    return dp


class ModelZAdnotacjaMixin(models.Model):
    adnotacja = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        abstract = True


class DostepnoscOgolnaMixin(models.Model):
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

    kolejnosc = models.PositiveSmallIntegerField(default=0, blank=False, null=False)

    tylko_dni_powszednie = models.BooleanField(default=False)

    def relevant_zakres_dat(self, dzien):
        assert dzien is not None

        attr_name = f"dzien_{dzien.isoweekday()}"
        if not getattr(self, attr_name):
            # Jeżeli ta reguła nie ma zastosowania do tego dnia tygodnia, to
            # nie sprawdzaj zakresu dat
            return False

        if self.start is None and self.koniec is None:
            return True

        if self.start is not None and self.start <= dzien and self.koniec is None:
            return True

        if self.start is None and self.koniec is not None and self.koniec >= dzien:
            return True

        if self.start is not None and self.koniec is not None and self.start <= dzien and self.koniec >= dzien:
            return True

    def czy_dostepny(self, dzien):
        if self.tylko_dni_powszednie:
            if Holiday.objects.is_holiday(dzien):
                return False

        n = dzien.isoweekday()
        attr = "dzien_%i" % n
        if getattr(self, attr):
            # Ta reguła ma zastosowanie do tego dnia tygodnia 'dzien'
            return self.dostepny

        return False

    class Meta:
        abstract = True
