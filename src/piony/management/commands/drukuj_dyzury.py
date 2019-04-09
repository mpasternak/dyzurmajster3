import locale
from datetime import datetime

from django.contrib.auth.models import User
from django.core.management import BaseCommand
from django.db import transaction

from piony.models import Grafik, Wydruk, nastepny_miesiac, koniec_miesiaca

locale.setlocale(locale.LC_ALL, '')


class Command(BaseCommand):
    def add_arguments(self, parser):
        from piony.utils import parse_date
        parser.add_argument('kod_wydruku', choices=[wydruk.kod for wydruk in Wydruk.objects.all()])
        parser.add_argument('--start', type=parse_date, default=nastepny_miesiac(datetime.now().date()))
        parser.add_argument('--koniec', type=parse_date, default=None)
        parser.add_argument('--username')

    @transaction.atomic
    def handle(self, kod_wydruku, start, koniec, username, *args, **options):
        if koniec is None:
            koniec = koniec_miesiaca(start)
        grafik = Grafik.objects.all().first()
        user = User.objects.get(username=username) if username else None
        print(Wydruk.objects.get(kod=kod_wydruku).drukuj(grafik, start, koniec, user=user))
