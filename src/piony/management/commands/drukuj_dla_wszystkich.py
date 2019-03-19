import locale
import os
from datetime import datetime

import progressbar
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
        parser.add_argument('--koniec', type=parse_date,
                            default=koniec_miesiaca(nastepny_miesiac(datetime.now().date())))
        parser.add_argument('--outdir')

    @transaction.atomic
    def handle(self, kod_wydruku, start, koniec, outdir, *args, **options):
        grafik = Grafik.objects.all().first()
        wydruk = Wydruk.objects.get(kod=kod_wydruku)
        for user in progressbar.progressbar(list(User.objects.all())):
            res = wydruk.drukuj(grafik, start, koniec, user=user)
            if not outdir:
                print(res)
                continue
            open(os.path.join(outdir, user.username + ".html"), "w").write(res)
