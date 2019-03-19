from collections import defaultdict
from datetime import timedelta, datetime

from django.core.exceptions import ValidationError
from django.db import models

from holidays.models import Holiday
from piony import const
from piony.models import Pion, poczatek_miesiaca, koniec_miesiaca, PionNiePracuje, Nierozpisany, Wolne, \
    poczatek_tygodnia, koniec_tygodnia
from piony.models.util import repr_user


class BlednyParametr(Exception):
    pass


def zakres_dat_lub_miesiac(start=None, koniec=None, miesiac=None):
    if start is None and koniec is None and miesiac is None:
        raise BlednyParametr("podaj start i koniec lub miesiac")

    if start is not None and koniec is not None and miesiac is not None:
        raise BlednyParametr("podane start, koniec, miesiac, ktorego mam uzyc?")

    if (start is not None and koniec is None) or (start is None and koniec is not None):
        raise BlednyParametr("start, koniec - jeden to None, a drugi nie, o co chodzi?")

    if miesiac is not None:
        start = poczatek_miesiaca(miesiac)
        koniec = koniec_miesiaca(miesiac)

    return start, koniec


def formatuj_miesieczny(tytul, dane, font_size="16pt"):
    header, rows = dane

    ret = ""

    def output(s):
        nonlocal ret
        ret += s

    output(
        "<head><meta charset=utf-8></head><body><style>* { font-family: Calibri; font-size: %s; } th { background: black; color: white; }</style>" % font_size)
    output(f"<h2>{tytul}</h2>")
    output("<table border=1 cellpadding=2 cellspacing=0 bordercolor=black>")
    output("<tr>")
    for elem in header:
        output(f"<th><center>{elem}</center></th>")
    output("</tr>")
    for dzien, elem in rows:
        if Holiday.objects.is_holiday(dzien):
            output("<tr bgcolor=#eeeeee>")
        else:
            output("<tr>")
        for n in elem:
            output(f"<td>{n}</td>")
        output("</tr>")
    output("</table>")
    output("<small>wygenerowane %s</small>" % datetime.now())
    output("</body>")

    return ret


def formatuj_tygodniowy(dane, bez_weekendow=True):
    header, rows = dane

    ret = ""

    def output(s):
        nonlocal ret
        ret += s

    output(
        "<head><meta charset=utf-8></head><body><style>* { font-family: 'Calibri'; font-size: 15pt; } th { background: #eeeeee; color:black; } @media print { .nextPage {page-break-before:always;}} </style>")

    starting_row = 0
    while True:
        # output(f"<center><h3>{tabela['tytul']}</h3></center>")
        output("<table border=1 bordercolor=black cellpadding=3 cellspacing=0>")
        for n_row in range(len(header)):
            output("<tr>")
            first_col_needed = True

            for elem in range(starting_row, starting_row + 5 if bez_weekendow else 7):
                if first_col_needed:
                    output(f"<th valign=top align=right class=firstCol><b>{header[n_row]}</b></th>")
                    first_col_needed = False

                if n_row == 0:
                    output(f"<th valign=top>{rows[elem][1][n_row]}</th>")
                else:
                    output(f"<td valign=top>{rows[elem][1][n_row]}</td>")

            output("</tr>")
        output("</table>")
        output("<small>wygenerowane %s</small>" % datetime.now())
        output("<div class=nextPage>")
        starting_row += 7
        if starting_row + 7 > len(rows):
            break
    output("</body>")

    return ret


class Wydruk(models.Model):
    kod = models.CharField(max_length=32, unique=True)
    nazwa = models.CharField(max_length=100, blank=True, null=True)
    font_size = models.CharField("Wielkość czcionki", max_length=10, blank=True, null=True, help_text="CSS font-size; może być w pt, px, em...")

    rodzaj = models.PositiveSmallIntegerField(
        choices=[
            (const.MIESIECZNY, "miesięczny"),
            (const.TYGODNIOWY, "tygodniowy")
        ]
    )

    class Meta:
        verbose_name = 'wydruk'
        verbose_name_plural = 'wydruki'

    def __str__(self):
        return self.kod

    def drukuj(self, grafik, start=None, koniec=None, miesiac=None, user=None):
        start, koniec = zakres_dat_lub_miesiac(start, koniec, miesiac)

        if self.rodzaj == const.MIESIECZNY:
            tytul = "Plan pracy na %s" % start.strftime("%b %Y")
            if user:
                tytul += " dla " + (f"{user.first_name} {user.last_name}".strip() or user.username)
            dane = self.dane(grafik, start=start, koniec=koniec, user=user)
            return formatuj_miesieczny(tytul, dane, font_size=self.font_size)

        elif self.rodzaj == const.TYGODNIOWY:
            start = poczatek_tygodnia(start)
            koniec = koniec_tygodnia(koniec)
            dane = self.dane(grafik, start=start, koniec=koniec, user=user)
            return formatuj_tygodniowy(dane)

        raise NotImplementedError

    def dane(self, grafik, start=None, koniec=None, miesiac=None, user=None):
        start, koniec = zakres_dat_lub_miesiac(start, koniec, miesiac)

        elementy = self.elementwydruku_set.all().order_by('kolejnosc')

        header = [element.header() for element in elementy]
        rows = []

        dzien = start
        while dzien <= koniec:
            row = []
            for elem in elementy:
                row.append(elem.value(dzien, grafik, user))
            rows.append((dzien, row))
            dzien += timedelta(days=1)
        return header, rows

    pass


kolumnaNaRodzaj = {
    const.KOLUMNA_PION_NOCNYSWIATECZNY: const.NOCNYSWIATECZNY,
    const.KOLUMNA_PION_DZIENNY: const.DZIENNY
}


class ElementWydruku(models.Model):
    wydruk = models.ForeignKey(Wydruk, models.CASCADE)

    rodzaj = models.PositiveSmallIntegerField(
        choices=[
            (const.KOLUMNA_DATA, "Data"),
            (const.KOLUMNA_DZIEN_TYGODNIA, "Dzień tygodnia"),
            (const.KOLUMNA_DZIEN_MIESIACA, "Dzień miesiąca"),
            (const.KOLUMNA_PION, "Pion"),
            (const.KOLUMNA_WOLNE, "Wolne"),
            (const.KOLUMNA_NIEROZPISANI, "Nierozpisani"),
            (const.KOLUMNA_PION_DZIENNY, "Pion dzienny"),
            (const.KOLUMNA_PION_NOCNYSWIATECZNY, "Pion dyżurowy")
        ]
    )

    pion = models.ForeignKey(Pion, models.CASCADE, blank=True, null=True)

    kolejnosc = models.PositiveSmallIntegerField(default=0, blank=False, null=False)

    class Meta:
        ordering = ['kolejnosc', ]
        verbose_name = 'element wydruku'
        verbose_name_plural = 'elementy wydruku'

    def __str__(self):
        return "element wydruku " + str(self.wydruk) + " nr " + str(self.kolejnosc)

    def clean(self):
        if self.rodzaj == const.KOLUMNA_PION:
            if self.pion is None:
                raise ValidationError({"pion": "Jeżeli typ kolumny to pion, to wybierz jakiś pion"})
        else:
            if self.pion is not None:
                raise ValidationError({"pion": "Piony wpisuj tylko dla typu kolumny 'Pion'"})

    def header(self):
        if self.rodzaj == const.KOLUMNA_DATA:
            return "Dzień"
        elif self.rodzaj == const.KOLUMNA_DZIEN_TYGODNIA:
            return "Dzień tygodnia"
        elif self.rodzaj == const.KOLUMNA_PION:
            return self.pion.nazwa
        elif self.rodzaj == const.KOLUMNA_NIEROZPISANI:
            return "Nierozpisani"
        elif self.rodzaj == const.KOLUMNA_WOLNE:
            return "Wolne"
        elif self.rodzaj == const.KOLUMNA_PION_DZIENNY:
            return "Pion dzienny"
        elif self.rodzaj == const.KOLUMNA_PION_NOCNYSWIATECZNY:
            return "Pion dyżurowy"
        elif self.rodzaj == const.KOLUMNA_DZIEN_MIESIACA:
            return "Dzień"

        raise ValueError(self.rodzaj)

    def value(self, dzien, grafik, user=None):
        if self.rodzaj == const.KOLUMNA_DATA:
            if Holiday.objects.is_holiday(dzien):
                return f"<b>{dzien}</b>"
            else:
                return f"{dzien}"

        elif self.rodzaj == const.KOLUMNA_DZIEN_MIESIACA:
            return f"<center>{dzien.day}</center>"

        elif self.rodzaj == const.KOLUMNA_DZIEN_TYGODNIA:
            return dzien.strftime("%A")

        elif self.rodzaj == const.KOLUMNA_WOLNE:
            ret = defaultdict(list)
            for wolne in Wolne.objects.filter(dzien=dzien, grafik=grafik):

                if wolne.przyczyna.startswith("po dyż"):
                    skrot = "☾"
                elif wolne.przyczyna == "wypoczynkowy":
                    skrot = "☀"
                elif wolne.przyczyna == "L4":
                    skrot = "L4"
                else:
                    skrot = wolne.przyczyna

                ret[skrot].append(repr_user(wolne.user))

            ret = [f"{przyczyna}&nbsp;{', '.join(ludzie)}" for przyczyna, ludzie in ret.items()]
            return "<br>".join(ret)

        elif self.rodzaj == const.KOLUMNA_NIEROZPISANI:
            ret = []
            for nierozpisany in Nierozpisany.objects.filter(dzien=dzien, grafik=grafik):
                ret.append(repr_user(nierozpisany.user))
            return ", ".join(ret)

        elif self.rodzaj == const.KOLUMNA_PION:
            try:
                pnp = PionNiePracuje.objects.get(dzien=dzien, pion=self.pion, grafik=grafik)
                return pnp.przyczyna
            except PionNiePracuje.DoesNotExist:
                pass

            ret = []
            for wpis in grafik.wpis_set.filter(dzien=dzien, pion=self.pion):
                ret.append(wpis.render())
            return "<br/>".join(ret)

        elif self.rodzaj in [const.KOLUMNA_PION_NOCNYSWIATECZNY, const.KOLUMNA_PION_DZIENNY]:
            ret = [wpis.pion.nazwa for wpis in
                   grafik.wpis_set.filter(dzien=dzien, user=user, pion__rodzaj=kolumnaNaRodzaj[self.rodzaj])]
            return ", ".join(ret)

        raise ValueError(self.rodzaj)
