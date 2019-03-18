from django.core.management import BaseCommand
from django.db import transaction

from piony.models import Grafik, Wydruk, ZyczeniaPracownika

import locale
locale.setlocale(locale.LC_ALL, '')

class Command(BaseCommand):
    def add_arguments(self, parser):
        from piony.utils import parse_date
        parser.add_argument('start', type=parse_date)
        parser.add_argument('koniec', type=parse_date)

    @transaction.atomic
    def handle(self, start, koniec, *args, **options):
        grafik = Grafik.objects.all().first()

        wydruki = [wydruk.drukuj(grafik, start, koniec) for wydruk in Wydruk.objects.filter(kod__startswith='DYZ')]

        open("output.html", "w").write(", ".join(wydruki))

        wydruki = []
        ind = Wydruk.objects.get(kod="IND")
        for zp in ZyczeniaPracownika.objects.all():
            wydruki.append(ind.drukuj(grafik, start, koniec, user=zp.user))
        open("ludzie.html", "w").write(", ".join(wydruki))

        import os
        os.system("open output.html")
        os.system("open ludzie.html")
