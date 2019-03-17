from datetime import timedelta
from uuid import uuid4

from dateutil import relativedelta
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.template import Template, Context, TemplateSyntaxError
from django.utils.functional import cached_property

from core.helpers import daterange
from holidays.models import Holiday
from piony import const
from piony.models.util import spacja_inicjal_z_kropka
from .pion import Pion, dostepne_piony
from .urlop import Urlop
from .zyczenia import ZyczeniaPracownika


def robil_w_dzien(dzien, zp, grafik):
    return Wpis.objects.filter(
        user=zp.user,
        grafik=grafik,
        dzien=dzien,
        pion__rodzaj=const.DZIENNY
    ).exists()


def ile_robil_czy_mial_dobe(dzien, zp, grafik):
    """Czy miał dobę danego dnia?"""

    godzin = 0

    for wpis in Wpis.objects.filter(user=zp.user, grafik=grafik, dzien=dzien):
        if wpis.pion.rodzaj == const.DZIENNY:
            godzin += 8
        elif wpis.pion.rodzaj == const.NOCNYSWIATECZNY:
            if Holiday.objects.is_holiday(dzien):
                godzin += 24
            else:
                godzin += 16
        else:
            raise ValueError(wpis.pion.rodzaj)

    return (godzin, godzin == 24)


class SwietoError(ValueError):
    pass


class NieznanyRodzajPionu(ValueError):
    pass


def ostatnio_pracowal_godzin_temu(chce_rozpisac, dzis, zp, grafik, delta=1):
    """"Maksymalna zwracana wartość to 24"""
    dzis_swieto = Holiday.objects.is_holiday(dzis)
    dzis_zwykly_dzien = not dzis_swieto
    wczoraj = dzis - timedelta(days=delta)

    if chce_rozpisac == const.DZIENNY:
        if dzis_swieto:
            raise SwietoError("Rozpisujesz dyzur dzienny w dzien swiateczny?")

        ile_robil, czy_mial_dobe = ile_robil_czy_mial_dobe(wczoraj, zp, grafik)

        if ile_robil == 0:
            return 24
        if ile_robil == 8:
            return 16
        if ile_robil == 16 or ile_robil == 24:
            return 0
    elif chce_rozpisac == const.NOCNYSWIATECZNY:
        if robil_w_dzien(dzis, zp, grafik) is True:
            return 0
        ile_robil, czy_mial_dobe = ile_robil_czy_mial_dobe(wczoraj, zp, grafik)
        if ile_robil == 24 or ile_robil == 16:
            return 8
        if ile_robil == 8:
            return 16
        if ile_robil == 0:
            return const.PONAD_24_GODZINY  # formalnie to 25, ale chodzi o symbol


def godziny_ciaglej_pracy(chce_rozpisac, dzis, zp, grafik):
    """
    Sprawdź - hipoteteycznie - ile godzin ciaglej pracy bedzie mial uzytkownik
    zp.user po rozpisaniu pionu typu 'chce_rozpisac' w dniu 'dzis'
    """

    def zlicz_ciaglosc_pracy(dzien_startowy):
        w_sumie_robil = 0
        dni_wstecz = 0
        while True:
            ile_robil, mial_dobe = ile_robil_czy_mial_dobe(
                dzien_startowy - timedelta(days=dni_wstecz), zp, grafik)

            if ile_robil in [16, 24]:
                w_sumie_robil += ile_robil

            dni_wstecz += 1

            if not mial_dobe:
                break

        return w_sumie_robil

    dzis_swieto = Holiday.objects.is_holiday(dzis)
    dzis_zwykly_dzien = not dzis_swieto
    wczoraj = dzis - timedelta(days=1)
    przedwczoraj = wczoraj - timedelta(days=1)

    if dzis_swieto and chce_rozpisac == const.DZIENNY:
        raise SwietoError

    if chce_rozpisac == const.DZIENNY:
        dzis_wypadnie = 8
    elif chce_rozpisac == const.NOCNYSWIATECZNY:
        if dzis_swieto:
            dzis_wypadnie = 24
        else:
            dzis_wypadnie = 16
    else:
        raise ValueError(chce_rozpisac)

    if chce_rozpisac == const.DZIENNY:
        return zlicz_ciaglosc_pracy(wczoraj) + dzis_wypadnie

    elif chce_rozpisac == const.NOCNYSWIATECZNY:
        if dzis_swieto:
            return zlicz_ciaglosc_pracy(wczoraj) + dzis_wypadnie

        # dzis_zwykly_dzienif dzis_zwykly_dzien:
        robil_rano = robil_w_dzien(dzis, zp, grafik)

        if robil_rano:
            return 8 + dzis_wypadnie + zlicz_ciaglosc_pracy(wczoraj)

        return dzis_wypadnie

    raise NieznanyRodzajPionu(chce_rozpisac)


def jakichs_w_miesiacu(dzien, zp, grafik, funkcja):
    return Wpis.objects.filter(
        grafik=grafik,
        user=zp.user,
        dzien__in=funkcja(dzien)
    ).count()


def dobowych_w_miesiacu(dzien, zp, grafik):
    return jakichs_w_miesiacu(dzien, zp, grafik, dni_swiateczne_w_miesiacu)


def zwyklych_w_miesiacu(dzien, zp, grafik):
    return jakichs_w_miesiacu(dzien, zp, grafik, dni_powszednie_w_miesiacu)


def poczatek_tygodnia(data):
    return data - timedelta(days=data.isoweekday() - 1)


def koniec_tygodnia(data):
    return poczatek_tygodnia(data) + timedelta(days=6)


def dni_jakies_w_miesiacu(data, holiday_status):
    for elem in daterange(poczatek_miesiaca(data), koniec_miesiaca(data)):
        if Holiday.objects.is_holiday(elem) == holiday_status:
            yield elem


def dni_swiateczne_w_miesiacu(data):
    return dni_jakies_w_miesiacu(data, holiday_status=True)


def dni_powszednie_w_miesiacu(data):
    return dni_jakies_w_miesiacu(data, holiday_status=False)


def dniowek_w_tygodniu(dzien, zp, grafik):
    return Wpis.objects.filter(
        grafik=grafik,
        user=zp.user,
        pion__rodzaj=const.DZIENNY,
        dzien__range=(poczatek_tygodnia(dzien), koniec_tygodnia(dzien))
    ).count()


def ostatni_rodzaj_pionu_dni_temu(dzien, zp, grafik, rodzaj):
    w = Wpis.objects.filter(
        grafik=grafik,
        user=zp.user,
        pion__rodzaj=rodzaj,
        dzien__lt=dzien
    ).order_by('-dzien').first()
    if w is None:
        return None
    return (dzien - w.dzien).days


def ostatnia_dniowka_dni_temu(dzien, zp, grafik):
    return ostatni_rodzaj_pionu_dni_temu(dzien, zp, grafik, const.DZIENNY)


def ostatni_dyzur_dni_temu(dzien, zp, grafik):
    return ostatni_rodzaj_pionu_dni_temu(dzien, zp, grafik, const.NOCNYSWIATECZNY)


def poczatek_miesiaca(dzien):
    return dzien.replace(day=1)


def koniec_miesiaca(dzien):
    return poczatek_miesiaca(dzien) + relativedelta.relativedelta(day=31)


def sprawdz_nie_dyzuruje_z(dzien, zp, grafik, rodzaj=const.NOCNYSWIATECZNY):
    """Sprawdz, czy w dniu 'dzien' ma dyzur osoba, ktora jest wymieniona
    w zp.nie_dyzuruje_z"""
    return Wpis.objects.filter(
        dzien=dzien,
        pion__rodzaj=rodzaj,
        grafik=grafik,
        user__in=zp.nie_dyzuruje_z.all()
    ).exists()


def rodzajow_wpisow_w_miesiacu(dzien, zp, grafik, rodzaj):
    return Wpis.objects.filter(
        grafik=grafik,
        user=zp.user,
        pion__rodzaj=rodzaj,
        dzien__range=(poczatek_miesiaca(dzien), koniec_miesiaca(dzien))
    ).count()


def dniowek_w_miesiacu(dzien, zp, grafik):
    return rodzajow_wpisow_w_miesiacu(dzien, zp, grafik, const.DZIENNY)


def dyzurow_w_miesiacu(dzien, zp, grafik):
    return rodzajow_wpisow_w_miesiacu(dzien, zp, grafik, const.NOCNYSWIATECZNY)


def dostepni_pracownicy(dzien, grafik):
    for zp in ZyczeniaPracownika.objects.all():
        # Sprawdź, czy ma tego dnia urlop
        try:
            urlop = zp.urlop_set.get(
                Q(start__range=(dzien, dzien)) |
                Q(koniec__range=(dzien, dzien)) |
                Q(start__lt=dzien, koniec__gt=dzien)
            )
            yield (zp, False, const.URLOP, urlop)
        except Urlop.DoesNotExist:
            pass

        # Sprawdź, czy ma przypisanie szczegółowe na ten dzień
        miesiac = dzien.replace(day=1)
        found = False
        for z in zp.zyczeniaszczegolowe_set.filter(miesiac_i_rok=miesiac):
            if dzien.day in z.dni():
                found = True
                yield (zp, True, const.SZCZEGOLOWE, z)
                break

        if found:
            continue

        # Sprawdź, czy ma przypisanie ogólne na ten dzień
        for z in zp.zyczeniaogolne_set.filter(
                Q(start=None, koniec=None) |

                Q(start=None, koniec__gte=dzien) |
                Q(start__lte=dzien, koniec=None) |

                Q(start__lte=dzien, koniec__gte=dzien)
        ).order_by('-kolejnosc'):
            n = dzien.isoweekday()
            attr = "dzien_%i" % n
            if getattr(z, attr):
                # Ta reguła ma zastosowanie do tego dnia tygodnia 'dzien'
                yield (zp, z.dostepny, const.OGOLNE, z)
                break


def czy_moglby_wziac(pion, dzien, pracownicy, grafik):
    """Zwraca listę osób z listy pracownicy (zp, status, const.PRZYCZNA, obiekt),
    które mogą wziąć ten pion w danym dniu wobec konkretnego grafiku. """

    for zp, moze, typ_zyczenia, zyczenie in pracownicy:
        if not moze:
            # Ten użytkownik NIE może wziąć tego dnia nic
            yield (zp, False, typ_zyczenia, zyczenie)
            continue

        # Ten użytkownik może wziąć coś tego dnia, sprawdźmy, czy ten pion:
        if pion not in zp.wszystkie_dozwolone_piony():
            # Ten użytkownik nie ma przypisania do tego pionu
            yield (zp, False, const.BRAK_PRZYPISANIA, pion)
            continue

        # Ten użytkownik ma ogólne przypisanie do tego pionu. Sprawdźmy,
        # czy to życzenie konkretnie tego pionu dotyczy:
        if zyczenie.pion is not None:
            if pion == zyczenie.pion:
                # Jeżeli w tym konkretnym pionie ma go NIE być, to nie:
                if not getattr(zyczenie, 'dostepny', True):
                    yield (zp, False, const.ZGLOSZONY_NIEDOSTEPNY_KONKRETNY_PION, zyczenie)
                    continue

        if zyczenie.rodzaj_pionu is not None:
            if pion.rodzaj == zyczenie.rodzaj_pionu:
                if not getattr(zyczenie, 'dostepny', True):
                    yield (zp, False, const.ZGLOSZONY_NIEDOSTEPNY_RODZAJ_PIONU, zyczenie)
                    continue

        # sprawdź maks_godzin_ciaglej_pracy
        gcp = godziny_ciaglej_pracy(pion.rodzaj, dzien, zp, grafik)
        if gcp > zp.maks_godzin_ciaglej_pracy:
            yield (zp, False, const.PRZEKROCZONY_CZAS_CIAGLEJ_PRACY, gcp)
            continue

        # sprawdź kiedy ostatnio pracował pod kątem rozpisania w dany pion:
        opgt = ostatnio_pracowal_godzin_temu(pion.rodzaj, dzien, zp, grafik) or 24
        if opgt < zp.min_odpoczynek_po_ciaglej_pracy:
            yield (zp, False, const.ZBYT_MALY_ODPOCZYNEK, opgt)
            continue

        if pion.rodzaj == const.DZIENNY:

            n = ostatnia_dniowka_dni_temu(dzien, zp, grafik)
            if n is not None and n < zp.dniowka_co_ile_dni:
                yield (zp, False, const.DNIOWKA_ZA_WCZESNIE, n)
                continue

            if zp.maks_dniowki is not None:
                n = dniowek_w_miesiacu(dzien, zp, grafik)
                if n >= zp.maks_dniowki:
                    yield (zp, False, const.MAKS_DNIOWKI_W_MIESIACU, n)
                    continue

            if zp.maks_dniowki_w_tygodniu is not None:
                n = dniowek_w_tygodniu(dzien, zp, grafik)
                if n >= zp.maks_dniowki_w_tygodniu:
                    yield (zp, False, const.MAKS_DNIOWKI_W_TYGODNIU, n)
                    continue

        elif pion.rodzaj == const.NOCNYSWIATECZNY:

            if zp.maks_dyzury is not None:
                n = dyzurow_w_miesiacu(dzien, zp, grafik)
                if n >= zp.maks_dyzury:
                    yield (zp, False, const.MAKS_DYZURY_W_MIESIACU, n)
                    continue

            n = ostatni_dyzur_dni_temu(dzien, zp, grafik)
            if n is not None and n < zp.dyzur_co_ile_dni:
                yield (zp, False, const.DYZUR_ZA_WCZESNIE, n)
                continue

            # sprawdz nie_dyzuruje_z
            if sprawdz_nie_dyzuruje_z(dzien, zp, grafik, pion.rodzaj) is True:
                yield (zp, False, const.NIE_DYZURUJE_Z, zp.nie_dyzuruje_z)
                continue

            if Holiday.objects.is_holiday(dzien):
                if zp.maks_dobowe is not None:
                    n = dobowych_w_miesiacu(dzien, zp, grafik)
                    if n >= zp.maks_dobowe:
                        yield (zp, False, const.MAKS_DYZURY_DOBOWE_W_MIESIACU, n)
                        continue
            else:
                if zp.maks_zwykle is not None:
                    n = zwyklych_w_miesiacu(dzien, zp, grafik)
                    if n >= zp.maks_zwykle:
                        yield (zp, False, const.MAKS_DYZURY_ZWYKLE_W_MIESIACU, n)
                        continue

        if not hasattr(zyczenie, 'dostepny'):
            yield (zp, True, const.SZCZEGOLOWE, zyczenie)
            continue

        yield (zp, zyczenie.dostepny, const.OGOLNE, zyczenie)


class Grafik(models.Model):
    uuid = models.UUIDField(default=uuid4(), editable=False, unique=True)
    miesiac = models.DateField()

    def uloz(self, start, koniec):

        # TODO: 2) popatrz na ich priorytety pionów
        # TODO: 3) rozpisz lekarzy wg priorytetów, kto co bardziej chce i kocha

        for dzien in daterange(start, koniec):

            piony = dostepne_piony(dzien)
            pracownicy = dostepni_pracownicy(dzien, grafik=self)

            moglby = {}
            for pion in piony:
                moglby[pion] = czy_moglby_wziac(pion, dzien, pracownicy, grafik=self)

            raise NotImplementedError

    pass


class BazaWpisuGrafika(models.Model):
    grafik = models.ForeignKey(Grafik, models.CASCADE)
    dzien = models.DateField(db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)

    class Meta:
        abstract = True


class Wolne(BazaWpisuGrafika):
    przyczyna = models.CharField(max_length=100)


class Wpis(BazaWpisuGrafika):
    pion = models.ForeignKey(Pion, models.CASCADE)
    template = models.TextField(
        default=None, blank=True, null=True,
        help_text="""{{user.last_name}} {{user.first_name|first|capfirst}}""")

    @cached_property
    def ile_godzin(self):
        if self.pion.rodzaj == const.NOCNYSWIATECZNY:
            if Holiday.objects.is_holiday(self.dzien):
                return 24
            else:
                return 16
        elif self.pion.rodzaj == const.DZIENNY:
            return 8

        raise ValueError("rodzaj pionu to %s, co mam z nim zrobic?" % self.pion.rodzaj)

    class Meta:
        unique_together = [
            ('user', 'dzien', 'pion')
        ]
        verbose_name_plural = 'wpisy'

    def clean(self):
        try:
            t = Template(self.template).render(Context())
        except TemplateSyntaxError:
            raise ValidationError({"template": "To nie jest poprawna templatka Django"})

    def __str__(self):
        return f"{self.dzien} {self.pion} {self.user}"

    def render(self):
        if self.template:
            return Template(self.template).render(
                Context(dict(user=self.user, dzien=self.dzien, pion=self.pion)))

        return f"{self.user.last_name}{spacja_inicjal_z_kropka(self.user.first_name)}"

    class Meta:
        unique_together = [
            ('user', 'dzien', 'pion')
        ]
        verbose_name_plural = 'wpisy'
