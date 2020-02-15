from datetime import datetime

from django.core.management import BaseCommand, CommandError
from django.db import transaction

from piony.models import Grafik, Wydruk, ZyczeniaPracownika, koniec_miesiaca

import locale

from piony.models.util import nastepny_miesiac

locale.setlocale(locale.LC_ALL, '')

class Command(BaseCommand):
    def add_arguments(self, parser):
        from piony.utils import parse_date
        parser.add_argument('--start', type=parse_date, default=nastepny_miesiac(datetime.now().date()))
        parser.add_argument('--koniec', type=parse_date, default=None)
        parser.add_argument(
            '--noinput', '--no-input', action='store_false', dest='interactive',
            help="Do NOT prompt the user for input of any kind.",
        )

    def handle(self, start, koniec, interactive, *args, **options):
        if koniec is None:
            koniec = koniec_miesiaca(start)

        if interactive:

            message = (
                'Ta opcja skasuje nadpisze domyślny grafik w zakresie dat od %s do %s. \n\n' % (start, koniec),
                "Wpisz 'tak' aby kontynuowac. "
            )
            if input(''.join(message)) != 'tak':
                raise CommandError("Anulowano.")

        grafik = Grafik.objects.all().first()
        with transaction.atomic():
            grafik.wyczysc_wpisy(start, koniec)
            grafik.uloz(start, koniec)
