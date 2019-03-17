from collections import defaultdict
from datetime import timedelta, date
from uuid import uuid4

from dateutil import relativedelta
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.template import Template, Context, TemplateSyntaxError
from django.utils.functional import cached_property
from mptt.fields import TreeForeignKey

from core.helpers import daterange
from holidays.models import Holiday
from piony import const
from .pion import Pion, dostepne_piony
from .urlop import Urlop
from .util import repr_user
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
        pion__rodzaj=const.NOCNYSWIATECZNY,
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
            continue
        except Urlop.DoesNotExist:
            pass

        # Sprawdź, czy ma przypisanie szczegółowe na ten dzień
        miesiac = dzien.replace(day=1)
        found = False
        for z in zp.zyczeniaszczegolowe_set.filter(miesiac_i_rok=miesiac):
            if dzien.day in z.dni():
                found = True
                yield (zp, True, const.ZYCZENIE, z)
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
                yield (zp, True, const.ZYCZENIE, z)


def czy_moglby_wziac(pion, dzien, w_pracy, grafik):
    """Zwraca listę osób z listy pracownicy (zp, status, const.PRZYCZNA, obiekt),
    które mogą wziąć ten pion w danym dniu wobec konkretnego grafiku. """

    for zp in w_pracy:
        # Ten użytkownik może wziąć coś tego dnia, sprawdźmy, czy ten pion:

        if dzien == date(2019, 4, 6) and zp.user.username == 'bgdula':
            print("X")
        if pion not in zp.wszystkie_dozwolone_piony():
            # Ten użytkownik nie ma przypisania do tego pionu
            yield (zp, False, const.BRAK_PRZYPISANIA, pion)
            continue

        dopasowanie = False
        for zyczenie in zp.zyczeniaszczegolowe_set.all():
            if zyczenie.relevant(pion, dzien):
                dopasowanie = True
                break

        if not dopasowanie:
            for zyczenie in zp.zyczeniaogolne_set.all().order_by("-kolejnosc"):
                if zyczenie.relevant(pion, dzien):
                    dopasowanie = True
                    break

        if not dopasowanie:
            yield (zp, False, const.NIEDOPASOWANE, None)
            # Życzenie nie jest dopasowane do pionu, nie analizuj dalszych
            # dostępności, czasów itp
            continue

        # Jeżeli mamy adekwatne do pionu/daty życzenie i mówi ono, ze
        # użytkownik NIE jest wówczas dostępny, to nie sprawdzaj, ile
        # pracował itp itd, tylko w tym momencie zwróć, że nie:
        if not getattr(zyczenie, 'dostepny', True):
            yield (zp, False, const.OGOLNE, zyczenie)

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

        yield (zp, True, const.ZYCZENIE, zyczenie)


class TrackerRozpisan:
    def __init__(self):
        self.wszyscy = set()
        self.rozpisani_dzien = set()
        self.rozpisani_noc = set()

    def nierozpisani(self):
        return self.wszyscy - self.rozpisani_dzien - self.rozpisani_noc

    def rozpisz(self, pion, pracownik):
        self.wszyscy.add(pracownik)
        if pion.rodzaj == const.NOCNYSWIATECZNY:
            self.rozpisani_noc.add(pracownik)
        elif pion.rodzaj == const.DZIENNY:
            self.rozpisani_dzien.add(pracownik)
        else:
            raise ValueError(pion.rodzaj)

    def rozpisany(self, pion, pracownik):
        if pion.rodzaj == const.NOCNYSWIATECZNY:
            if pracownik in self.rozpisani_noc:
                return True
        elif pion.rodzaj == const.DZIENNY:
            if pracownik in self.rozpisani_dzien:
                return True
        else:
            raise ValueError(pion.rodzaj)


class Grafik(models.Model):
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    nazwa = models.CharField(max_length=100, blank=True, null=True)
    pion_dla_nierozpisanych = models.ForeignKey(Pion, models.SET_NULL, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'grafiki'
        verbose_name = 'grafik'

    def uloz(self, start, koniec):

        for dzien in daterange(start, koniec):
            piony = list(dostepne_piony(dzien))
            posortowane_piony = [pion for pion, status, przyczyna in piony if status]
            posortowane_piony.sort(key=lambda pion: pion.priorytet)

            for urlop in Urlop.objects.filter(
                    Q(start__range=(dzien, dzien)) |
                    Q(koniec__range=(dzien, dzien)) |
                    Q(start__lt=dzien, koniec__gt=dzien)
            ):
                self.wolne_set.create(
                    dzien=dzien,
                    user=urlop.parent.user,
                    przyczyna=urlop.rodzaj
                )

            # W tym momencie pracownicy to lista (zp, status, obiekt) zawierająca
            # wszystkich pracownikow. Jezeli pracownik niedostepny, to status to False,
            # a obiekt to np. Urlop. Jezeli pracownik dostepny, to status to True, a obiekt
            # to pierwsze pasujące do tego dnia życzenie
            pracownicy = list(dostepni_pracownicy(dzien, grafik=self))

            w_pracy = set([pracownik for pracownik, status, przyczyna, obiekt in pracownicy if status])

            rezultaty = {}

            wolne_po_dyzurze = set()
            for pion, dostepny, przyczyna in piony:
                if not dostepny:
                    self.pionniepracuje_set.create(
                        pion=pion,
                        dzien=dzien,
                        przyczyna=przyczyna
                    )
                    continue
                lista = list(czy_moglby_wziac(pion, dzien, w_pracy, grafik=self))

                if pion.rodzaj == const.DZIENNY:
                    # Jeżeli ktokolwiek dla dziennego pionu ma przekroczonoe cokolwiek zwiazanego
                    # z czasem pracy przy rozpisywaniu na pion dzienny to zaznacz go jako "wolne po dyżurze"
                    for zp, status, przyczyna, obiekt in lista:
                        if not status:
                            if przyczyna in [const.ZBYT_MALY_ODPOCZYNEK, const.PRZEKROCZONY_CZAS_CIAGLEJ_PRACY]:
                                wolne_po_dyzurze.add(zp.user)

                rezultaty[pion] = lista

            for user in wolne_po_dyzurze:
                self.wolne_set.create(
                    user=user,
                    dzien=dzien,
                    przyczyna="po dyż"
                )

            dostepni = {}
            for pion, rezultat in rezultaty.items():
                # rezultat: tuple(zp, status, przyczyna, obiekt)
                dostepni[pion] = [zp for zp, status, przyczyna, obiekt in rezultat if status]

            # Na ile mozliwych pionow mozna rozpisac danego lekarza
            mozliwosci = defaultdict(int)
            for zps in dostepni.values():
                for zp in zps:
                    mozliwosci[zp] += 1

            for pion in dostepni.keys():
                dostepni[pion].sort(
                    key=lambda obj: (obj.priorytet_pionu(dzien, pion), mozliwosci[obj]))

            for rodzaj in const.DZIENNY, const.NOCNYSWIATECZNY:
                tr = TrackerRozpisan()

                for pion in [pion for pion in posortowane_piony if pion.rodzaj == rodzaj]:
                    pracownicy = dostepni.get(pion)

                    tr.wszyscy = set(pracownicy)

                    if not pracownicy:
                        print(pion, "brak obsady")
                        continue

                    for pracownik in pracownicy:
                        if tr.rozpisany(pion, pracownik):
                            continue

                        w = self.wpis_set.create(
                            user=pracownik.user,
                            dzien=dzien,
                            pion=pion
                        )
                        print(pion, w.user)
                        tr.rozpisz(pion, pracownik)
                        break

                if rodzaj == const.DZIENNY:
                    for nierozpisany in tr.nierozpisani():
                        if self.pion_dla_nierozpisanych:
                            self.wpis_set.create(
                                user=nierozpisany.user,
                                dzien=dzien,
                                pion=self.pion_dla_nierozpisanych
                            )
                            print("nierozpisany", nierozpisany.user, "=>", self.pion_dla_nierozpisanych)
                            continue

                        self.nierozpisany_set.create(
                            user=nierozpisany.user,
                            dzien=dzien
                        )
                        print("nierozpisany", nierozpisany.user)

    def wyczysc_wpisy(self, start, koniec):
        for rec_set in [self.wpis_set, self.pionniepracuje_set, self.wolne_set, self.nierozpisany_set]:
            rec_set.filter(
                dzien__range=(start, koniec)
            ).delete()


class BazaWpisuGrafika(models.Model):
    grafik = models.ForeignKey(Grafik, models.CASCADE)
    dzien = models.DateField(db_index=True)

    zmodyfikowano = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BazaWpisuUzytkownika(BazaWpisuGrafika):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)

    class Meta:
        abstract = True


class PionNiePracuje(BazaWpisuGrafika):
    pion = models.ForeignKey(Pion, models.CASCADE)
    przyczyna = models.CharField(max_length=100)


class Wolne(BazaWpisuUzytkownika):
    przyczyna = models.CharField(max_length=100)


class Nierozpisany(BazaWpisuUzytkownika):
    pass


class Wpis(BazaWpisuUzytkownika):
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

        ret = repr_user(self.user)
        return ret

    class Meta:
        unique_together = [
            ('user', 'dzien', 'pion')
        ]
        verbose_name_plural = 'wpisy'

def dzienne():
    raise NotImplementedError
nocneswiateczne = dzienne



class ZestawiajRazem(models.Model):
    parent = models.ForeignKey(Grafik, models.CASCADE)
    dzienny = TreeForeignKey(Pion, models.CASCADE, limit_choices_to={"rodzaj": const.DZIENNY}, related_name="+")
    nocnyswiateczny = TreeForeignKey(Pion, models.CASCADE,
                                        limit_choices_to={"rodzaj": const.NOCNYSWIATECZNY},
                                        related_name="+")
