import locale
from datetime import datetime

from django.contrib.auth.models import User
from django.core.management import BaseCommand
from django.db import transaction

from core.helpers import daterange
from holidays.models import Holiday
from piony import const
from piony.models import Grafik, nastepny_miesiac, koniec_miesiaca, dostepne_piony, Pion, ZyczeniaPracownika, Wpis

locale.setlocale(locale.LC_ALL, '')


class Command(BaseCommand):
    def add_arguments(self, parser):
        from piony.utils import parse_date
        parser.add_argument('--start', type=parse_date, default=nastepny_miesiac(datetime.now().date()))
        parser.add_argument('--koniec', type=parse_date, default=None)
        parser.add_argument('--pion')
        parser.add_argument('--username')

    @transaction.atomic
    def handle(self, start, koniec, username, pion, *args, **options):
        user = None

        if koniec is None:
            koniec = koniec_miesiaca(start)

        if username:
            user = User.objects.get(username=username)
            zp = ZyczeniaPracownika.objects.get(user=user)

        pion_nadrzedny = Pion.objects.get(nazwa="Szpital")
        if pion:
            pion_nadrzedny = Pion.objects.get(nazwa=pion)

        grafik = Grafik.objects.all().first()

        godziny_dzienne = {
            "wszystkie": 0,
            "emeryt": 0,
            "emeryt_bez_specjalizacji": 0,
            "nieobsadzone": 0,
            "niespecjalista": 0,
            "specjalista": 0
        }

        godziny_dyzurowe = {
            "wszystkie": 0,
            "emeryt": 0,
            "emeryt_bez_specjalizacji": 0,
            "nieobsadzone": 0,
            "niespecjalista": 0,
            "specjalista": 0,
        }

        dni = 0
        dni_swiateczne = 0

        for dzien in daterange(start, koniec):
            dni += 1
            if Holiday.objects.is_holiday(dzien):
                dni_swiateczne += 1

            dp = set([pion for pion, dostepny, przyczyna in dostepne_piony(dzien) if dostepny])
            if pion_nadrzedny:
                dp = [p for p in dp if p in pion_nadrzedny.get_descendants()]

            for pion in dp:

                ile = pion.ile_godzin(dzien)

                dct = godziny_dyzurowe
                if ile <= 8:
                    dct = godziny_dzienne

                dct['wszystkie'] += ile

                wpis = Wpis.objects.filter(dzien=dzien, pion=pion).first()
                if not wpis:
                    dct['nieobsadzone'] += ile
                    continue

                try:
                    zp = ZyczeniaPracownika.objects.get(user=wpis.user)
                except ZyczeniaPracownika.DoesNotExist:
                    raise Exception(wpis.user)

                if zp.emeryt:
                    dct['emeryt'] += ile

                if zp.specjalizacja != const.SPECJALISTA:
                    dct['niespecjalista'] += ile
                    if zp.emeryt:
                        dct['emeryt_bez_specjalizacji'] += ile
                else:
                    dct['specjalista'] += ile

        print("Start\t", start)
        print("Koniec\t", koniec)
        if pion_nadrzedny:
            print("Pion nadrzedny\t", pion_nadrzedny.nazwa)
        print("Dni\t", dni)
        print("Swieta\t", dni_swiateczne)

        def procenty(dct, label):
            total = dct['wszystkie']
            print(label, "\t", total, "godzin")
            for key, value in dct.items():
                if key == 'wszystkie':
                    continue
                print("\t", key, "\t", value, "godzin\t", "%.2f %%" % (value * 100.0 / total))

        procenty(godziny_dzienne, "Dniówki")
        procenty(godziny_dyzurowe, "Dyżury")
