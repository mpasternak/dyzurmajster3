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
        grafik.wyczysc_wpisy(start, koniec)
        grafik.uloz(start, koniec)
