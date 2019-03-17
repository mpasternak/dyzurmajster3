from django.core.management import BaseCommand
from django.core.management import BaseCommand
from django.db import transaction

from piony.models import Grafik, Wydruk


class Command(BaseCommand):
    def add_arguments(self, parser):
        from piony.utils import parse_date
        parser.add_argument('start', type=parse_date)
        parser.add_argument('koniec', type=parse_date)

    @transaction.atomic
    def handle(self, start, koniec, *args, **options):
        grafik = Grafik.objects.all().first()
        grafik.wyczysc_wpisy(start, koniec)
        grafik.uloz(start, koniec)

        wydruk = Wydruk.objects.get(kod='DYZ-1')
        res = wydruk.formatuj_miesieczny(start, grafik)

        wydruk = Wydruk.objects.get(kod='DYZ-2')
        res2 = wydruk.formatuj_miesieczny(start, grafik)

        wydruk = Wydruk.objects.get(kod='DYZ-3')
        res3 = wydruk.formatuj_miesieczny(start, grafik)

        open("output.html", "w").write(res + "<hr>" + res2 + "<hr>" + res3)
        import os
        os.system("open output.html")
