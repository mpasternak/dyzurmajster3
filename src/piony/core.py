from collections import defaultdict
from datetime import timedelta, date
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from holidays.models import Holiday
from piony import const
from piony.models import Pion
from piony.models.grafik import Wpis


def dostepne_piony(dzien):
    holiday = Holiday.objects.is_holiday(dzien)
    map = {
        True: [const.NOCNYSWIATECZNY],
        False: [const.DZIENNY, const.NOCNYSWIATECZNY]
    }

    for pion in Pion.objects.filter(rodzaj__in=map[holiday]).order_by('-priorytet', 'nazwa'):
        for regula in pion.dostepnoscpionu_set.all().order_by("-kolejnosc"):
            if regula.relevant(dzien):
                if regula.dostepny:
                    yield pion
                break
    yield Pion.objects.get(nazwa="L4")
    yield Pion.objects.get(nazwa="Urlop")

def dyzury_w_poprzednich_dobach(user, dzien):
    ret = 0
    while True:
        dzien = dzien - timedelta(days=1)
        c = Wpis.objects.filter(pion__rodzaj=const.NOCNYSWIATECZNY, user=user, dzien=dzien)
        if c.count() > 0:
            ret += 1
            continue
        break
    return ret


def praca_w_tej_dobie(user, dzien):
    try:
        w = Wpis.objects.get(user=user, dzien=dzien)
        if w.pion.rodzaj == const.NOCNYSWIATECZNY:
            if Holiday.objects.is_holiday(dzien):
                return 24
            return 16
        return 8

    except Wpis.DoesNotExist:
        return 0


def dyzury_w_tym_miesiacu(user, dzien):
    y = dzien.year
    m = dzien.month
    poczatek = date(y, m, 1)
    m += 1
    if m == 13:
        y += 1
        m = 1
    koniec = date(y, m, 1)

    zwykle = 0
    swiateczne = 0
    for elem in Wpis.objects.filter(
            user=user,
            dzien__gte=poczatek,
            dzien__lt=koniec,
            pion__rodzaj=const.NOCNYSWIATECZNY):
        if Holiday.objects.is_holiday(elem.dzien):
            swiateczne += 1
        else:
            zwykle += 1
    return zwykle, swiateczne


_users_cache = None


def cached_users():
    global _users_cache
    if _users_cache is None:
        _users_cache = dict(
            [(x, x.dostepnosc_set.all().order_by("-kolejnosc").select_related("pion", "user")) for x in
            User.objects.all().select_related('profil').prefetch_related("dostepnosc_set", "dostepnosc_set__pion")])

    return _users_cache

def dostepni_ludzie(pion, dzien):
    for user in cached_users().keys():
        for regula in cached_users()[user]:

            if regula.relevant(pion, dzien):
                if regula.dostepny:

                    try:
                        user.profil
                    except ObjectDoesNotExist:
                        yield (True, user)
                        break

                    if pion.rodzaj == const.NOCNYSWIATECZNY:
                        # Planujemy dyzur. Ile dyzurow mial w poprzednich dobach?
                        d = dyzury_w_poprzednich_dobach(user, dzien)
                        if d >= user.profil.dyzurow_w_ciagu:
                            break

                        if user.profil.maks_dobowe is not None or user.profil.maks_zwykle is not None:
                            zwykle, dobowe = dyzury_w_tym_miesiacu(user, dzien)

                            # Czy zakladany dyzur jest swiateczny?
                            h = Holiday.objects.is_holiday(dzien)

                            if h:
                                if user.profil.maks_dobowe is not None:
                                    if user.profil.maks_dobowe <= dobowe:
                                        break
                            else:
                                if user.profil.maks_zwykle is not None:
                                    if user.profil.maks_zwykle <= zwykle:
                                        break

                    elif pion.rodzaj == const.DZIENNY:
                        if user.profil.schodzi is True:
                            if dyzury_w_poprzednich_dobach(user, dzien) > 0:
                                yield (False, user)
                                break

                    # Obsługa reguł "do 2 dyżurów od 15 do 30"
                    if regula.ilosc is not None:
                        pion_kw = {}
                        if regula.rodzaj_pionu is not None:
                            pion_kw = {"pion__rodzaj": regula.rodzaj_pionu}
                        c = Wpis.objects.filter(
                            user=user,
                            dzien__gte=regula.start,
                            dzien__lte=regula.koniec,
                            **pion_kw
                        ).count()
                        if c >= regula.ilosc:
                            break

                    yield (True, user)

                break


def uloz_dyzury(od_dnia, do_dnia):
    while od_dnia <= do_dnia:
        print(f"---[{ od_dnia }]---------------------------")

        dp = list(dostepne_piony(od_dnia))
        dl = {}
        pd = {}

        zajeci_dzien = set()
        zajeci_dyzur = set()

        dostepni_dzien = set()
        dostepni_dyzur = set()

        wagi_dzien = defaultdict(int)
        wagi_dyzur = defaultdict(int)

        for pion in dp:
            dost = list(dostepni_ludzie(pion, od_dnia))
            pd[pion] = [x[1] for x in dost if not x[0]]
            dl[pion] = [x[1] for x in dost if x[0]]

            if pion.rodzaj == const.NOCNYSWIATECZNY:
                wagi = wagi_dyzur
                dostepni = dostepni_dyzur
            elif pion.rodzaj == const.DZIENNY:
                wagi = wagi_dzien
                dostepni= dostepni_dzien
            elif pion.rodzaj == const.POZA_PRACA:
                for pracownik in dl[pion]:
                    Wpis.objects.create(dzien=od_dnia, user=pracownik, pion=pion)
                    zajeci_dzien.add(pracownik)
                    zajeci_dyzur.add(pracownik)
                continue
            else:
                raise NotImplementedError(pion.rodzaj)

            for pracownik in dl[pion]:
                dostepni.add(pracownik)
                wagi[pracownik] += 1

        for pion in dp:
            if pion.rodzaj == const.NOCNYSWIATECZNY:
                wagi = wagi_dyzur
            elif pion.rodzaj == const.DZIENNY:
                wagi = wagi_dzien
            elif pion.rodzaj == const.POZA_PRACA:
                continue
            else:
                raise NotImplementedError(pion.rodzaj)

            dl[pion].sort(key=lambda key: wagi[key])

        for pion in dp:
            if pion.rodzaj == const.NOCNYSWIATECZNY:
                zajetosc = zajeci_dyzur
                wagi = wagi_dyzur
            elif pion.rodzaj == const.DZIENNY:
                zajetosc = zajeci_dzien
                wagi = wagi_dzien
            elif pion.rodzaj == const.POZA_PRACA:
                continue
            else:
                raise NotImplementedError(pion.rodzaj)

            kolejka = []
            if pion.rodzaj == const.NOCNYSWIATECZNY:
                # Kolejka do dyżuru uwzględniająca równy podział dyżurów
                for czlowiek in dl[pion]:
                    if czlowiek in zajetosc:
                        continue
                    zwykle, swiateczne = dyzury_w_tym_miesiacu(czlowiek, od_dnia)
                    if Holiday.objects.is_holiday(od_dnia):
                        s = swiateczne
                    else:
                        s = zwykle

                    profil = None
                    priorytet = 0
                    try:
                        profil = czlowiek.profil
                        priorytet = profil.priorytet_pionu(od_dnia, pion)
                        if priorytet is None:
                            priorytet = profil.priorytet
                    except ObjectDoesNotExist:
                        pass

                    # Ta osoba nie pracuje tego dnia, ale moze juz jest rozpisany ktos,
                    # kto jest oznaczony w tabelce "nie dyzuruje z..."
                    if profil is not None:
                        collision = False
                        for elem in profil.nie_dyzuruje_z.all():
                            if elem in zajetosc:
                                collision = True
                                break
                        if collision:
                            continue

                    # Czy został zachowany minimalny odstęp dyżurów
                    if profil is not None:
                        if profil.dni_pomiedzy_dyzurami:
                            ostatni_dyzur = Wpis.objects.filter(
                                user=czlowiek,
                                pion__rodzaj=const.NOCNYSWIATECZNY,
                                dzien__lt=od_dnia).order_by("-dzien").first()
                            if ostatni_dyzur is not None:
                                dystans = (od_dnia - ostatni_dyzur.dzien).days - 1
                                if dystans < profil.dni_pomiedzy_dyzurami:
                                    continue

                    kolejka.append((s, wagi[czlowiek], 100 - priorytet, czlowiek))

                kolejka.sort(key=lambda key: (key[0], key[1], key[2]))
                print("Kolejka do ", pion)
                print(kolejka)
                kolejka = [k[3] for k in kolejka]
            else:
                # Kolejka do dniówek uwzględniająca priorytet
                for czlowiek in dl[pion]:
                    if czlowiek in zajetosc:
                        continue

                    profil = None
                    try:
                        profil = czlowiek.profil
                        priorytet = profil.priorytet_pionu(od_dnia, pion)
                    except ObjectDoesNotExist:
                        priorytet = 50
                        pass
                    kolejka.append((100 - priorytet, wagi[czlowiek], czlowiek))

                print("Kolejka do ", pion)
                kolejka.sort(key=lambda key: (key[0], key[1]))
                print(kolejka)
                kolejka = [k[2] for k in kolejka]

            if kolejka:
                Wpis.objects.create(
                    dzien=od_dnia,
                    user=kolejka[0],
                    pion=pion)
                print(od_dnia, "% 30s" % pion, kolejka[0])
                zajetosc.add(kolejka[0])

        # Utwórz wpisy dla nierozdysponowanych ludzi na dniu
        nierozdysponowani = dostepni_dzien - zajeci_dzien
        for czlowiek in nierozdysponowani:
            print(od_dnia, "% 30s" % 'Nierozdysponowany -', czlowiek)
            Wpis.objects.create(dzien=od_dnia, user=czlowiek, pion=Pion.objects.get(nazwa="Nierozpisany"))

        po_dyz = set()
        for pion, lekarze in pd.items():
            for elem in lekarze:
                po_dyz.add(elem)

        for czlowiek in po_dyz:
            if czlowiek not in nierozdysponowani:
                print(od_dnia, "% 30s" % "Po dyżurze -", czlowiek)
                Wpis.objects.create(dzien=od_dnia, user=czlowiek, pion=Pion.objects.get(nazwa="Po dyżurze"))

        od_dnia += timedelta(days=1)
