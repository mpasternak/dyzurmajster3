import locale
from collections import defaultdict
from datetime import datetime, date

from django.contrib.auth.models import User
from django.core.management import BaseCommand
from django.db import transaction

from core.helpers import daterange
from piony import const
from piony.models import Grafik, nastepny_miesiac, koniec_miesiaca, dostepne_piony, Pion, ZyczeniaPracownika

locale.setlocale(locale.LC_ALL, '')


class Command(BaseCommand):
    def add_arguments(self, parser):
        from piony.utils import parse_date
        parser.add_argument('--start', type=parse_date, default=nastepny_miesiac(datetime.now().date()))
        parser.add_argument('--koniec', type=parse_date,
                            default=koniec_miesiaca(nastepny_miesiac(datetime.now().date())))
        parser.add_argument('--username')

    @transaction.atomic
    def handle(self, start, koniec, username, *args, **options):
        user = None
        if username:
            user = User.objects.get(username=username)
            zp = ZyczeniaPracownika.objects.get(user=user)

        grafik = Grafik.objects.all().first()
        nieobsadzone = defaultdict(list)
        obsadzone = defaultdict(list)
        piony = dict([(pion.pk, pion) for pion in Pion.objects.all()])
        for dzien in daterange(start, koniec):
            dp = set([pion.pk for pion, dostepny, przyczyna in dostepne_piony(dzien) if dostepny])
            wpisy = grafik.wpis_set.filter(dzien=dzien).values_list("pion", flat=True)
            nieobsadzone[dzien] = dp.difference(wpisy)
            obsadzone[dzien] = wpisy

        nieobsadzone_ranki = set()
        nieobsadzone_dyzury = set()

        nieobsadzone_dla_usera = set()
        for dzien, lista_pionow in nieobsadzone.items():
            if not lista_pionow:
                # wszystko obsadzone, hura!
                continue

            if user:
                moze_wziac = False

                if dzien == date(2019, 4, 29):
                    print("X")

                czy_jest_w_grafiku = grafik.wpis_set.filter(dzien=dzien, user=user).exists()
                czy_ma_urlop = zp.czy_ma_urlop(dzien)

                if not czy_jest_w_grafiku and not czy_ma_urlop:
                    # Tego dnia ten user nie pracuje więc może coś wziąć:
                    for nieobsadzony_pion in lista_pionow:
                        if piony[nieobsadzony_pion] in zp.wszystkie_dozwolone_piony():
                            nieobsadzone_dla_usera.add((dzien, piony[nieobsadzony_pion], ""))
                            continue

                        ### TODO: szukanie zamian dyżurowych
                        # w przypadku dyżurów nocnych użyj reguł i sprawdź grafik
                        # czy dany user moze wziac dany dyzur, bo potem sie okaze
                        # ze costam.

                        # TODO: sprawdzaj czy da sie usera zamienic na dyzury -- do 3
                        # poziomów "wgłąb". to moze byc istotne bo to moze ewentualnie
                        # bardziej wypelnić grafik ORAZ będzie można tego użyc
                        # przy układaniu dyżurów

                        # Najwyrazniej nie znalezlismy pionu, ktory ten uzytkownik
                        # mógłby wziąć. Sprawdźmy, czy z tego dnia możemy zrelokować
                        # kogoś z innego pionu na ten, w kórym brakuje człowieka:
                        for obsadzony_pion in Pion.objects.filter(
                                rodzaj=piony[nieobsadzony_pion].rodzaj,
                                pk__in=obsadzone[dzien]).exclude(pk=nieobsadzony_pion):

                            do_przesuniecia = grafik.wpis_set.get(pion=obsadzony_pion, dzien=dzien)
                            try:
                                do_przesuniecia.user.zyczeniapracownika
                            except:
                                continue

                            stan1, przyczyna1, obiekt1 = do_przesuniecia.user.zyczeniapracownika.czy_ma_regule_pozwalajaca_wziac(piony[nieobsadzony_pion], dzien)

                            stan2, przyczyna2, obiekt2 = zp.czy_ma_regule_pozwalajaca_wziac(obsadzony_pion, dzien)
                            print("Sprwadzam, czy %s moze wziac %s => %s" % (do_przesuniecia.user, piony[nieobsadzony_pion], stan1))
                            print("Sprawdzam czy %s moze wziac %s => %s" % (user, obsadzony_pion, stan2))
                            if stan1 and stan2:
                                nieobsadzone_dla_usera.add((dzien, piony[nieobsadzony_pion], "pod warunkiem, że %s z %s -> %s" % (
                                    do_przesuniecia,
                                    obsadzony_pion.nazwa,
                                    piony[nieobsadzony_pion].nazwa)))
                                break

            print(dzien, ", ".join([piony[pion].nazwa for pion in lista_pionow]))

            for pion in lista_pionow:
                p = piony[pion]
                if p.rodzaj == const.NOCNYSWIATECZNY:
                    nieobsadzone_dyzury.add((dzien, pion))
                else:
                    nieobsadzone_ranki.add((dzien, pion))

        for label, tablica in ("dyżury", nieobsadzone_dyzury), ("ranki", nieobsadzone_ranki):
            print(label, "do wzięcia:")
            for dzien, pion in sorted(tablica):
                print("\t*", dzien, piony[pion])

        if user:
            def wypisz(rodzaj=const.DZIENNY):
                for dzien, pion, komentarz in sorted(nieobsadzone_dla_usera, key=lambda obj: obj[0]):
                    if pion.rodzaj == rodzaj:
                        print("\t", dzien.day, pion, komentarz)

            print(f"{username} moze wziac dniówki:")
            wypisz(const.DZIENNY)

            print(f"{username} moze wziac dyżury:")
            wypisz(const.NOCNYSWIATECZNY)
