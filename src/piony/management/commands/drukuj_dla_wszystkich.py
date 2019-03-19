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
        parser.add_argument('--koniec', type=parse_date,
                            default=koniec_miesiaca(nastepny_miesiac(datetime.now().date())))

    @transaction.atomic
    def handle(self, kod_wydruku, start, koniec, *args, **options):
        grafik = Grafik.objects.all().first()
        user = User.objects.get(username=username) if username else None
        print(Wydruk.objects.get(kod=kod_wydruku).drukuj(grafik, start, koniec, user=user))


# wydruki = [wydruk.drukuj(grafik, start, koniec) for wydruk in Wydruk.objects.filter(kod__startswith='DYZ')]
#
# open("output.html", "w").write(", ".join(wydruki))
#
# wydruki = []
# ind = Wydruk.objects.get(kod="IND")
# for zp in ZyczeniaPracownika.objects.all():
#     wydruki.append(ind.drukuj(grafik, start, koniec, user=zp.user))
# open("ludzie.html", "w").write(", ".join(wydruki))
#
# import os
# os.system("open output.html")
# os.system("open ludzie.html")
