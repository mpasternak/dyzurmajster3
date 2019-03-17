from datetime import timedelta, datetime

from django.core.exceptions import ValidationError
from django.db import models

from holidays.models import Holiday
from piony import const
from piony.models import Pion, Wpis, poczatek_miesiaca, koniec_miesiaca


class Wydruk(models.Model):
    kod = models.CharField(max_length=32, unique=True)
    nazwa = models.CharField(max_length=100, blank=True, null=True)

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

    def drukuj(self, data, grafik):
        if self.rodzaj == const.MIESIECZNY:
            return self.formatuj_miesieczny(data, grafik)
        raise NotImplementedError

    def miesieczny(self, miesiac, grafik):
        poczatek = poczatek_miesiaca(miesiac)
        koniec = koniec_miesiaca(miesiac)

        elementy = self.elementwydruku_set.all().order_by('kolejnosc')

        header = [element.header() for element in elementy]
        rows = []

        dzien = poczatek
        while dzien <= koniec:
            row = []
            for elem in elementy:
                row.append(elem.value(dzien, grafik))
            rows.append((dzien, row))
            dzien += timedelta(days=1)
        return header, rows

    def formatuj_miesieczny(self, miesiac, grafik):
        header, rows = self.miesieczny(miesiac, grafik)

        ret = ""

        def output(s):
            nonlocal ret
            ret += s

        output(
            "<head><meta charset=utf-8></head><body><style>* { font-family: Calibri; font-size: 16pt; } th { background: black; color: white; }</style>")
        output("<h2>Dyżury na %s</h2>" % miesiac.strftime("%b %Y"))
        output("<table border=1 cellpadding=2 cellspacing=0 bordercolor=black>")
        output("<tr>")
        for elem in header:
            output(f"<th>{elem}</th>")
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

    pass


class ElementWydruku(models.Model):
    wydruk = models.ForeignKey(Wydruk, models.CASCADE)

    rodzaj = models.PositiveSmallIntegerField(
        choices=[
            (const.KOLUMNA_DZIEN, "Dzień"),
            (const.KOLUMNA_DZIEN_TYGODNIA, "Dzień tygodnia"),
            (const.KOLUMNA_PION, "Pion")
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

    def header(self):
        if self.rodzaj == const.KOLUMNA_DZIEN:
            return "Dzień"
        elif self.rodzaj == const.KOLUMNA_DZIEN_TYGODNIA:
            return "Dzień tygodnia"
        elif self.rodzaj == const.KOLUMNA_PION:
            return self.pion.nazwa

        raise ValueError(self.rodzaj)

    def value(self, dzien, grafik):
        if self.rodzaj == const.KOLUMNA_DZIEN:
            if Holiday.objects.is_holiday(dzien):
                return f"<b>{dzien}</b>"
            else:
                return f"{dzien}"
        elif self.rodzaj == const.KOLUMNA_DZIEN_TYGODNIA:
            return dzien.strftime("%A")
        else:
            ret = []
            for wpis in Wpis.objects.filter(dzien=dzien, pion=self.pion, grafik=grafik):
                ret.append(wpis.render())
            return ", ".join(ret)

        raise ValueError(self.rodzaj)
