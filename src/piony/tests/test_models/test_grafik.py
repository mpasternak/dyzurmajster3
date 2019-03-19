from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from model_mommy import mommy

from piony import const
from piony.models import Wpis, dostepni_pracownicy, czy_moglby_wziac, godziny_ciaglej_pracy, ile_robil_czy_mial_dobe, \
    robil_w_dzien, ostatnio_pracowal_godzin_temu, ostatnia_dniowka_dni_temu, dniowek_w_miesiacu, dniowek_w_tygodniu, \
    poczatek_tygodnia, koniec_tygodnia, dyzurow_w_miesiacu, ostatni_dyzur_dni_temu, ZyczeniaPracownika, \
    sprawdz_nie_dyzuruje_z, dni_swiateczne_w_miesiacu, dni_powszednie_w_miesiacu, dobowych_w_miesiacu, \
    zwyklych_w_miesiacu, SwietoError, Pion, Wydruk


def test_grafik_wpis_clean():
    w = Wpis(template="kopara {%a jakze%}")
    with pytest.raises(ValidationError):
        w.clean()

    w = Wpis(template="{{hey}}")
    w.clean()


def test_grafik_wpis_str(wpis):
    assert str(wpis) != None


def test_grafik_wpis_render(wpis):
    ret = wpis.render()
    assert len(ret) > 1


def test_grafik_wpis_render_2(wpis):
    wpis.template = "123"
    assert wpis.render() == "123"


def test_grafik_wpis_render_2(wpis):
    wpis.template = "{{dzien.day}}"
    assert wpis.render() == "1"


def test_dostepni_pracownicy_urlop(zp, nowy_rok):
    zp.urlop_set.create(
        start=nowy_rok,
        koniec=nowy_rok,
        rodzaj="wypoczynkowy"
    )
    l = list(dostepni_pracownicy(nowy_rok, grafik=None))
    zyczenia, dostepny, przyczyna, obiekt = l[0]
    assert not dostepny
    assert przyczyna == const.URLOP


def test_dostepni_pracownicy_zyczenie_szczegolowe(zp, nowy_rok):
    zp.zyczeniaszczegolowe_set.create(
        miesiac_i_rok=nowy_rok,
        lista_dni="1"
    )
    l = list(dostepni_pracownicy(nowy_rok, grafik=None))
    zyczenia, dostepny, przyczyna, obiekt = l[0]
    assert dostepny
    assert przyczyna == const.ZYCZENIE


def test_dostepni_pracownicy_zyczenie_ogolne(zp, nowy_rok):
    zp.zyczeniaogolne_set.create(
        adnotacja="Etat"
    )
    l = list(dostepni_pracownicy(nowy_rok, grafik=None))
    zyczenia, dostepny, przyczyna, obiekt = l[0]
    assert dostepny
    assert przyczyna == const.ZYCZENIE


@pytest.fixture
def dyzurant(zp, pion_nocny):
    zp.dozwolone_piony.add(pion_nocny)
    zp.zyczeniaogolne_set.create(
        adnotacja="Ciagly dyzur",
        rodzaj_pionu=const.NOCNYSWIATECZNY
    )
    return zp


@pytest.fixture
def etatowy(zp, pion_dzienny):
    zp.dozwolone_piony.add(pion_dzienny)
    zp.zyczeniaogolne_set.create(
        adnotacja="Etat!",
        rodzaj_pionu=const.DZIENNY
    )
    return zp


def test_poczatek_tygodnia(poniedzialek, wtorek, sroda, czwartek, niedziela):
    for elem in [poniedzialek, wtorek, sroda, czwartek, niedziela]:
        assert poczatek_tygodnia(elem) == poniedzialek


def test_koniec_tygodnia(poniedzialek, wtorek, sroda, czwartek, niedziela):
    for elem in [poniedzialek, wtorek, sroda, czwartek, niedziela]:
        assert koniec_tygodnia(elem) == niedziela


@pytest.mark.django_db
def test_ostatnia_dniowka_dni_temu(sroda, czwartek, pion_dzienny, pion_nocny, zp, grafik):
    assert ostatnia_dniowka_dni_temu(czwartek, zp, grafik) is None
    grafik.wpis_set.create(
        user=zp.user,
        dzien=sroda,
        pion=pion_dzienny
    )
    grafik.wpis_set.create(
        user=zp.user,
        dzien=czwartek,
        pion=pion_nocny
    )
    for cnt in range(10):
        assert ostatnia_dniowka_dni_temu(czwartek + timedelta(days=cnt), zp, grafik) == cnt + 1


@pytest.mark.django_db
def test_ostatni_dyzur_dni_temu(sroda, czwartek, pion_dzienny, pion_nocny, zp, grafik):
    assert ostatni_dyzur_dni_temu(czwartek, zp, grafik) is None
    grafik.wpis_set.create(
        user=zp.user,
        dzien=sroda,
        pion=pion_dzienny
    )
    grafik.wpis_set.create(
        user=zp.user,
        dzien=czwartek,
        pion=pion_nocny
    )
    assert ostatni_dyzur_dni_temu(czwartek, zp, grafik) is None
    for cnt in range(1, 10):
        assert ostatni_dyzur_dni_temu(czwartek + timedelta(days=cnt), zp, grafik) == cnt


@pytest.mark.django_db
def test_sprawdz_nie_dyzuruje_z(nowy_rok, pion_nocny, zp, grafik):
    user2 = mommy.make(User)
    zp2 = ZyczeniaPracownika.objects.create(user=user2)

    assert sprawdz_nie_dyzuruje_z(nowy_rok, zp, grafik) is False

    zp.nie_dyzuruje_z.add(user2)

    grafik.wpis_set.create(
        dzien=nowy_rok,
        pion=pion_nocny,
        user=user2
    )

    assert sprawdz_nie_dyzuruje_z(nowy_rok, zp, grafik) is True


@pytest.mark.django_db
def test_dniowek_w_tygodniu(wtorek, sroda, czwartek, pion_dzienny, pion_nocny, zp, grafik):
    grafik.wpis_set.create(
        user=zp.user,
        dzien=sroda,
        pion=pion_dzienny
    )
    grafik.wpis_set.create(
        user=zp.user,
        dzien=sroda,
        pion=pion_nocny
    )
    grafik.wpis_set.create(
        user=zp.user,
        dzien=czwartek,
        pion=pion_dzienny
    )
    assert dniowek_w_tygodniu(wtorek, zp, grafik) == 2


def oni_mogliby_wziac(pion, dzien, grafik=None):
    dp = dostepni_pracownicy(dzien, grafik=grafik)
    w_pracy = [pracownik for pracownik, status, przyczyna, obiekt in dp if status]
    return list(czy_moglby_wziac(pion, dzien, w_pracy, grafik=grafik))


def czy_dyzurant_wezmie(dyzurant, dzien, pion, grafik=None):
    lista = oni_mogliby_wziac(pion, dzien, grafik)
    for zp, moze, przyczyna, obiekt in lista:
        if zp == dyzurant:
            return zp, moze, przyczyna, obiekt


def test_czy_moglby_wziac(dyzurant, pion_nocny, nowy_rok):
    dyzurant, moze, przyczyna, obiekt = czy_dyzurant_wezmie(dyzurant, nowy_rok, pion_nocny)
    assert moze


def test_czy_moglby_wziac_zly_rodzaj_pionu(dyzurant, pion_dzienny, sroda):
    dyzurant, moze, przyczyna, obiekt = czy_dyzurant_wezmie(dyzurant, sroda, pion_dzienny)
    assert not moze


def test_czy_moglby_wziac_zly_rodzaj_pionu_2(etatowy, pion_nocny, nowy_rok):
    dyzurant, moze, przyczyna, obiekt = czy_dyzurant_wezmie(etatowy, nowy_rok, pion_nocny)
    assert not moze


def test_czy_moglby_wziac_brak_przypisania(dyzurant, pion_dzienny, sroda):
    dyzurant, moze, przyczyna, obiekt = czy_dyzurant_wezmie(dyzurant, sroda, pion_dzienny)
    assert not moze
    assert przyczyna == const.BRAK_PRZYPISANIA


def test_czy_moglby_wziac_przekroczony_czas_pracy(grafik, dyzurant, nowy_rok, sroda, pion_nocny, pion_dzienny):
    dyzurant.maks_godzin_ciaglej_pracy = 32
    dyzurant.dozwolone_piony.add(pion_dzienny)

    zo = dyzurant.zyczeniaogolne_set.create(
        rodzaj_pionu=const.DZIENNY,
        adnotacja="Etat"
    )
    assert zo.relevant(pion_dzienny, sroda)

    dyzurant.save()

    grafik.wpis_set.create(
        user=dyzurant.user,
        pion=pion_nocny,
        dzien=nowy_rok
    )

    dyzurant, moze, przyczyna, obiekt = czy_dyzurant_wezmie(dyzurant, sroda, pion_dzienny, grafik)
    assert moze, przyczyna

    dyzurant.maks_godzin_ciaglej_pracy = 24
    dyzurant.save()
    dyzurant, moze, przyczyna, obiekt = czy_dyzurant_wezmie(dyzurant, sroda, pion_dzienny, grafik)
    assert not moze
    assert przyczyna == const.PRZEKROCZONY_CZAS_CIAGLEJ_PRACY


def test_czy_moglby_wziac_zbyt_maly_odpoczynek(grafik, dyzurant, nowy_rok, sroda, czwartek, pion_nocny, pion_dzienny):
    dyzurant.min_odpoczynek_po_ciaglej_pracy = 11
    dyzurant.dozwolone_piony.add(pion_dzienny)
    dyzurant.save()

    grafik.wpis_set.create(
        user=dyzurant.user,
        pion=pion_nocny,
        dzien=nowy_rok
    )

    dyzurant.zyczeniaogolne_set.create(
        rodzaj_pionu=const.DZIENNY,
        adnotacja="Etat"
    )

    dyzurant, moze, przyczyna, obiekt = czy_dyzurant_wezmie(dyzurant, sroda, pion_dzienny, grafik)
    assert not moze
    dyzurant, moze, przyczyna, obiekt = czy_dyzurant_wezmie(dyzurant, czwartek, pion_dzienny, grafik)
    assert moze, przyczyna

    dyzurant.min_odpoczynek_po_ciaglej_pracy = 24
    dyzurant.save()
    dyzurant, moze, przyczyna, obiekt = czy_dyzurant_wezmie(dyzurant, sroda, pion_dzienny, grafik)
    assert not moze
    dyzurant, moze, przyczyna, obiekt = czy_dyzurant_wezmie(dyzurant, czwartek, pion_dzienny, grafik)
    assert moze

    dyzurant.min_odpoczynek_po_ciaglej_pracy = 30
    dyzurant.save()
    dyzurant, moze, przyczyna, obiekt = czy_dyzurant_wezmie(dyzurant, sroda, pion_dzienny, grafik)
    assert not moze
    dyzurant, moze, przyczyna, obiekt = czy_dyzurant_wezmie(dyzurant, czwartek, pion_dzienny, grafik)
    assert not moze


def test_czy_moglby_wziac_nieodstepny_w_tym_pionie_oglne_1(dyzurant, pion_nocny, nowy_rok):
    dyzurant.zyczeniaogolne_set.create(
        start=nowy_rok,
        koniec=nowy_rok,
        dostepny=False,
        adnotacja="Nie moze w nowy rok",
        kolejnosc=1
    )
    dyzurant, moze, przyczyna, obiekt = czy_dyzurant_wezmie(dyzurant, nowy_rok, pion_nocny)
    assert not moze
    assert przyczyna == const.OGOLNE


def test_czy_moglby_wziac_nieodstepny_w_tym_pionie_oglne_2(dyzurant, pion_nocny, nowy_rok):
    dyzurant.zyczeniaogolne_set.create(
        pion=pion_nocny,
        dostepny=False,
        kolejnosc=1
    )
    dyzurant, moze, przyczyna, obiekt = czy_dyzurant_wezmie(dyzurant, nowy_rok, pion_nocny)
    assert not moze
    assert przyczyna == const.OGOLNE


def test_czy_moglby_wziac_ogolnie_nieodstepny_w_tym_pionie_ale_jest_szczegolowe(dyzurant, pion_nocny, nowy_rok):
    dyzurant.zyczeniaogolne_set.all().delete()

    dyzurant.zyczeniaogolne_set.create(
        start=nowy_rok,
        koniec=nowy_rok,
        dostepny=False,
        kolejnosc=1,
        adnotacja="W nowy rok nie moze"
    )

    dyzurant.zyczeniaszczegolowe_set.create(
        pion=pion_nocny,
        miesiac_i_rok=nowy_rok,
        lista_dni="1"
    )
    dyzurant, moze, przyczyna, obiekt = czy_dyzurant_wezmie(dyzurant, nowy_rok, pion_nocny)
    assert moze, obiekt
    assert przyczyna == const.ZYCZENIE, obiekt


def test_czy_moglby_wziac_przekroczone_dniowki(zp, etatowy, pion_dzienny, sroda):
    etatowy.maks_dniowki = 0
    etatowy.save()

    etatowy, moze, przyczyna, obiekt = czy_dyzurant_wezmie(etatowy, sroda, pion_dzienny)
    assert not moze
    assert przyczyna == const.MAKS_DNIOWKI_W_MIESIACU


def test_czy_moglby_wziac_przekroczone_dniowki_w_tygodniu(zp, etatowy, pion_dzienny, sroda):
    etatowy.maks_dniowki_w_tygodniu = 0
    etatowy.save()

    etatowy, moze, przyczyna, obiekt = czy_dyzurant_wezmie(etatowy, sroda, pion_dzienny)
    assert not moze
    assert przyczyna == const.MAKS_DNIOWKI_W_TYGODNIU


def test_czy_moglby_wziac_przekroczone_dyzury(zp, dyzurant, pion_nocny, nowy_rok):
    dyzurant.maks_dyzury = 0
    dyzurant.save()

    dyzurant, moze, przyczyna, obiekt = czy_dyzurant_wezmie(dyzurant, nowy_rok, pion_nocny)
    assert not moze
    assert przyczyna == const.MAKS_DYZURY_W_MIESIACU


def test_czy_moglby_wziac_przekroczone_dobowe(zp, dyzurant, pion_nocny, nowy_rok):
    dyzurant.maks_dobowe = 0
    dyzurant.save()

    dyzurant, moze, przyczyna, obiekt = czy_dyzurant_wezmie(dyzurant, nowy_rok, pion_nocny)
    assert not moze
    assert przyczyna == const.MAKS_DYZURY_DOBOWE_W_MIESIACU


def test_czy_moglby_wziac_przekroczone_zwykle(zp, dyzurant, pion_nocny, sroda):
    dyzurant.maks_zwykle = 0
    dyzurant.save()

    dyzurant, moze, przyczyna, obiekt = czy_dyzurant_wezmie(dyzurant, sroda, pion_nocny)
    assert not moze
    assert przyczyna == const.MAKS_DYZURY_ZWYKLE_W_MIESIACU


def test_Grafik_uloz(grafik, nowy_rok, luty):
    """
    Jest 2 piony nocne, 1 dzienny

    Jest dwóch użytkowników z czego jeden ma etat i dyżury w obydwu pionach,

    drugi z kolei ma pojedyncze dyżury w pionie nocnym pierwszym, bez etatu.
    """
    pion_dzienny = mommy.make(Pion, nazwa='Dzienny', rodzaj=const.DZIENNY)
    pion_nocny = mommy.make(Pion, nazwa='Nocny 1', rodzaj=const.NOCNYSWIATECZNY)
    pion_nocny_drugi = mommy.make(Pion, nazwa='Nocny 2', rodzaj=const.NOCNYSWIATECZNY)

    user1 = mommy.make(User, username='User 1')
    zp1 = ZyczeniaPracownika.objects.create(
        user=user1,
    )
    zp1.dozwolone_piony.add(pion_dzienny, pion_nocny, pion_nocny_drugi)
    zp1.zyczeniaogolne_set.create(
        rodzaj_pionu=const.DZIENNY,
        adnotacja='Etat',
    )
    zp1.zyczeniaszczegolowe_set.create(
        rodzaj_pionu=const.NOCNYSWIATECZNY,
        lista_dni="2,5,10"
    )

    user2 = mommy.make(User, username='User 2')
    zp2 = ZyczeniaPracownika.objects.create(
        user=user2
    )
    zp2.dozwolone_piony.add(pion_nocny)
    zp2.zyczeniaszczegolowe_set.create(
        miesiac_i_rok=nowy_rok,
        lista_dni="1,2,5,10",
        adnotacja="Zyczenia dyzurowe"
    )

    grafik.uloz(nowy_rok, luty)

    assert grafik.wpis_set.get(
        dzien="2019-01-10",
        pion=pion_nocny,
    ).user == user2

    w = Wydruk.objects.create(kod='W1', rodzaj=const.MIESIECZNY)
    w.elementwydruku_set.create(
        rodzaj=const.KOLUMNA_DATA,
        kolejnosc=1
    )
    w.elementwydruku_set.create(
        rodzaj=const.KOLUMNA_DZIEN_TYGODNIA,
        kolejnosc=2
    )
    w.elementwydruku_set.create(
        rodzaj=const.KOLUMNA_PION,
        pion=pion_nocny,
        kolejnosc=3
    )
    w.elementwydruku_set.create(
        rodzaj=const.KOLUMNA_PION,
        pion=pion_nocny_drugi,
        kolejnosc=4
    )

    res = w.drukuj(grafik, miesiac=nowy_rok)
    assert len(res) > 1


def test_ile_robil_czy_mial_dobe_swieto(zp, pion_dzienny, pion_nocny, nowy_rok, grafik):
    assert ile_robil_czy_mial_dobe(nowy_rok, zp, grafik) == (0, False)
    grafik.wpis_set.create(
        user=zp.user,
        pion=pion_nocny,
        dzien=nowy_rok
    )
    assert ile_robil_czy_mial_dobe(nowy_rok, zp, grafik) == (24, True)


def test_ile_robil_czy_mial_dobe_zwykly_dzien(zp, pion_dzienny, pion_nocny, sroda, grafik):
    assert ile_robil_czy_mial_dobe(sroda, zp, grafik) == (0, False)

    grafik.wpis_set.create(
        user=zp.user,
        pion=pion_dzienny,
        dzien=sroda
    )
    assert ile_robil_czy_mial_dobe(sroda, zp, grafik) == (8, False)


def test_ile_robil_czy_mial_dobe_zwykly_noc(zp, pion_dzienny, pion_nocny, sroda, czwartek, grafik):
    assert ile_robil_czy_mial_dobe(sroda, zp, grafik) == (0, False)

    grafik.wpis_set.create(
        user=zp.user,
        pion=pion_nocny,
        dzien=sroda
    )
    assert ile_robil_czy_mial_dobe(sroda, zp, grafik) == (16, False)


def test_ile_robil_czy_mial_dobe_zwykly_doba(zp, pion_dzienny, pion_nocny, sroda, grafik):
    assert ile_robil_czy_mial_dobe(sroda, zp, grafik) == (0, False)

    grafik.wpis_set.create(
        user=zp.user,
        pion=pion_nocny,
        dzien=sroda
    )
    grafik.wpis_set.create(
        user=zp.user,
        pion=pion_dzienny,
        dzien=sroda
    )
    assert ile_robil_czy_mial_dobe(sroda, zp, grafik) == (24, True)


def test_czy_robil_rano(zp, pion_dzienny, pion_nocny, nowy_rok, grafik):
    assert robil_w_dzien(nowy_rok, zp, grafik) is False

    grafik.wpis_set.create(
        user=zp.user, pion=pion_dzienny, dzien=nowy_rok
    )
    assert robil_w_dzien(nowy_rok, zp, grafik) is True


def test_dniowek_w_miesiacu(zp, nowy_rok, sroda, czwartek, pion_dzienny, grafik):
    assert dniowek_w_miesiacu(nowy_rok, zp, grafik) == 0
    grafik.wpis_set.create(
        user=zp.user,
        dzien=sroda,
        pion=pion_dzienny

    )
    assert dniowek_w_miesiacu(nowy_rok, zp, grafik) == 1
    grafik.wpis_set.create(
        user=zp.user,
        dzien=czwartek,
        pion=pion_dzienny

    )
    assert dniowek_w_miesiacu(nowy_rok, zp, grafik) == 2


def test_dyzurow_w_miesiacu(zp, nowy_rok, sroda, czwartek, pion_nocny, grafik):
    assert dyzurow_w_miesiacu(nowy_rok, zp, grafik) == 0
    grafik.wpis_set.create(
        user=zp.user,
        dzien=sroda,
        pion=pion_nocny

    )
    assert dyzurow_w_miesiacu(nowy_rok, zp, grafik) == 1
    grafik.wpis_set.create(
        user=zp.user,
        dzien=czwartek,
        pion=pion_nocny

    )
    assert dyzurow_w_miesiacu(nowy_rok, zp, grafik) == 2


def test_ostatnio_pracowal_godzin_temu(zp, pion_dzienny, pion_nocny, wtorek, sroda, czwartek, grafik):
    assert ostatnio_pracowal_godzin_temu(
        const.DZIENNY, sroda, zp, grafik) == 24

    grafik.wpis_set.create(
        dzien=wtorek,
        pion=pion_nocny,
        user=zp.user
    )
    assert ostatnio_pracowal_godzin_temu(
        const.DZIENNY, sroda, zp, grafik) == 0

    assert ostatnio_pracowal_godzin_temu(
        const.NOCNYSWIATECZNY, sroda, zp, grafik) == 8

    assert ostatnio_pracowal_godzin_temu(
        const.DZIENNY, czwartek, zp, grafik) == 24

    grafik.wpis_set.create(
        dzien=sroda,
        pion=pion_dzienny,
        user=zp.user
    )
    assert ostatnio_pracowal_godzin_temu(
        const.DZIENNY, czwartek, zp, grafik) == 16


def test_godzin_ciaglej_pracy_po_dobie(zp, pion_dzienny, pion_nocny, nowy_rok, grafik, sroda, czwartek, piatek):
    # nowy_rok to wtorek, swieto
    with pytest.raises(SwietoError):
        godziny_ciaglej_pracy(const.DZIENNY, nowy_rok, zp, grafik)

    assert godziny_ciaglej_pracy(const.NOCNYSWIATECZNY, nowy_rok, zp, grafik) == 24
    assert ostatnio_pracowal_godzin_temu(const.NOCNYSWIATECZNY, nowy_rok, zp, grafik) == const.PONAD_24_GODZINY

    grafik.wpis_set.create(
        dzien=nowy_rok,
        user=zp.user,
        pion=pion_nocny
    )

    assert godziny_ciaglej_pracy(const.DZIENNY, sroda, zp, grafik) == 32
    assert ostatnio_pracowal_godzin_temu(const.DZIENNY, sroda, zp, grafik) == 0

    assert godziny_ciaglej_pracy(const.NOCNYSWIATECZNY, sroda, zp, grafik) == 16
    assert ostatnio_pracowal_godzin_temu(const.NOCNYSWIATECZNY, sroda, zp, grafik) == 8

    grafik.wpis_set.create(
        dzien=sroda,
        user=zp.user,
        pion=pion_dzienny
    )

    assert godziny_ciaglej_pracy(const.NOCNYSWIATECZNY, sroda, zp, grafik) == 48
    assert ostatnio_pracowal_godzin_temu(const.NOCNYSWIATECZNY, sroda, zp, grafik) == 0

    assert godziny_ciaglej_pracy(const.NOCNYSWIATECZNY, czwartek, zp, grafik) == 16
    assert ostatnio_pracowal_godzin_temu(const.NOCNYSWIATECZNY, czwartek, zp, grafik) == 16

    grafik.wpis_set.create(
        dzien=sroda,
        user=zp.user,
        pion=pion_nocny
    )
    assert godziny_ciaglej_pracy(const.DZIENNY, czwartek, zp, grafik) == 56
    assert godziny_ciaglej_pracy(const.NOCNYSWIATECZNY, czwartek, zp, grafik) == 16
    grafik.wpis_set.create(
        dzien=czwartek,
        user=zp.user,
        pion=pion_dzienny
    )
    assert godziny_ciaglej_pracy(const.NOCNYSWIATECZNY, czwartek, zp, grafik) == 24 * 3


def test_godzin_ciaglej_pracy(zp, pion_dzienny, pion_nocny, nowy_rok, grafik, sroda, czwartek, piatek):
    assert godziny_ciaglej_pracy(const.DZIENNY, sroda, zp, grafik) == 8
    assert godziny_ciaglej_pracy(const.NOCNYSWIATECZNY, sroda, zp, grafik) == 16

    grafik.wpis_set.create(
        dzien=sroda,
        user=zp.user,
        pion=pion_dzienny
    )
    assert godziny_ciaglej_pracy(const.NOCNYSWIATECZNY, sroda, zp, grafik) == 24

    sroda_noc = grafik.wpis_set.create(
        dzien=sroda,
        pion=pion_nocny,
        user=zp.user
    )
    assert godziny_ciaglej_pracy(const.DZIENNY, czwartek, zp, grafik) == 32
    assert godziny_ciaglej_pracy(const.NOCNYSWIATECZNY, czwartek, zp, grafik) == 16

    grafik.wpis_set.create(
        dzien=czwartek,
        user=zp.user,
        pion=pion_dzienny
    )

    assert godziny_ciaglej_pracy(const.DZIENNY, czwartek, zp, grafik) == 32
    assert godziny_ciaglej_pracy(const.NOCNYSWIATECZNY, czwartek, zp, grafik) == 48

    grafik.wpis_set.create(
        dzien=czwartek,
        pion=pion_nocny,
        user=zp.user
    )

    assert godziny_ciaglej_pracy(const.DZIENNY, piatek, zp, grafik) == 56

    grafik.wpis_set.create(
        dzien=piatek,
        pion=pion_dzienny,
        user=zp.user
    )

    assert godziny_ciaglej_pracy(const.NOCNYSWIATECZNY, piatek, zp, grafik) == 72

    sroda_noc.delete()

    assert godziny_ciaglej_pracy(const.DZIENNY, czwartek, zp, grafik) == 8
    assert godziny_ciaglej_pracy(const.NOCNYSWIATECZNY, czwartek, zp, grafik) == 24
    assert godziny_ciaglej_pracy(const.DZIENNY, piatek, zp, grafik) == 32
    assert godziny_ciaglej_pracy(const.NOCNYSWIATECZNY, piatek, zp, grafik) == 48


@pytest.mark.django_db
def test_dni_swiateczne_w_miesiacu(niedziela):
    assert len(list(dni_swiateczne_w_miesiacu(niedziela))) == 9


@pytest.mark.django_db
def test_dni_powszednie_w_miesiacu(niedziela):
    assert len(list(dni_powszednie_w_miesiacu(niedziela))) == 22


@pytest.mark.django_db
def test_dobowych_w_miesiacu(sroda, niedziela, grafik, zp, pion_nocny):
    grafik.wpis_set.create(
        user=zp.user,
        pion=pion_nocny,
        dzien=sroda
    )
    assert dobowych_w_miesiacu(sroda, zp, grafik) == 0
    grafik.wpis_set.create(
        user=zp.user,
        pion=pion_nocny,
        dzien=niedziela
    )
    assert dobowych_w_miesiacu(sroda, zp, grafik) == 1


@pytest.mark.django_db
def test_zwyklych_w_miesiacu(sroda, niedziela, grafik, zp, pion_nocny):
    grafik.wpis_set.create(
        user=zp.user,
        pion=pion_nocny,
        dzien=niedziela
    )
    assert zwyklych_w_miesiacu(sroda, zp, grafik) == 0

    grafik.wpis_set.create(
        user=zp.user,
        pion=pion_nocny,
        dzien=sroda
    )
    assert zwyklych_w_miesiacu(sroda, zp, grafik) == 1
