from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from model_mommy import mommy

from piony.models import ZyczeniaSzczegolowe, ZyczeniaOgolne, Pion


def test_ZyczeniaSzczegolowe():
    m = ZyczeniaSzczegolowe(miesiac_i_rok=date(2019, 1, 1))
    m.lista_dni = "1,2,3"
    assert m.clean() is None


def test_ZyczeniaOgolne(zp):
    m = ZyczeniaOgolne(parent=zp, adnotacja="kopara")
    assert "kopara" in str(m)


def test_ZyczeniaPracownika(zp):
    assert str(zp) is not None


@pytest.mark.parametrize("zyczenia_set,extra_args", [
    ("zyczeniaogolne_set", {}),
    ("zyczeniaszczegolowe_set", {"miesiac_i_rok": date(2019, 4, 1)})
])
def test_BazaZyczen_sprawdza_piony_nadrzedne(zp, zyczenia_set, extra_args):
    dozwolonyPion = mommy.make(Pion)
    niedozwolonyPion = mommy.make(Pion)

    zp.dozwolone_piony.add(dozwolonyPion)

    zyczenia_set = getattr(zp, zyczenia_set)
    obj = zyczenia_set.create(
        pion=niedozwolonyPion, **extra_args
    )
    with pytest.raises(ValidationError):
        obj.clean()

    obj2 = zyczenia_set.create(
        pion=dozwolonyPion, **extra_args
    )
    obj2.clean()


def test_priorytet_pionu(zp, pion_dzienny, pion_nocny, nowy_rok, luty):
    zp.priorytet_bazowy = 99
    zp.save()

    priorytet = zp.priorytet_set.create(
        start=nowy_rok,
        koniec=luty,
    )
    priorytet.piony.add(pion_nocny)

    assert zp.priorytet_pionu(nowy_rok, pion_dzienny) == 99
    assert zp.priorytet_pionu(nowy_rok, pion_nocny) == 50
    assert zp.priorytet_pionu(luty, pion_nocny) == 50
    assert zp.priorytet_pionu(luty + timedelta(days=5), pion_nocny) == 99


def test_ZyczeniaOgolne_relevant_zakres_dat(wtorek, sroda, czwartek, piatek):
    z = ZyczeniaOgolne(start=None, koniec=None)
    assert z.relevant_zakres_dat(wtorek)
    assert z.relevant_zakres_dat(sroda)
    assert z.relevant_zakres_dat(czwartek)

    z = ZyczeniaOgolne(start=None, koniec=wtorek)
    assert z.relevant_zakres_dat(wtorek)
    assert not z.relevant_zakres_dat(sroda)
    assert not z.relevant_zakres_dat(czwartek)

    z = ZyczeniaOgolne(start=sroda, koniec=None)
    assert not z.relevant_zakres_dat(wtorek)
    assert z.relevant_zakres_dat(sroda)
    assert z.relevant_zakres_dat(czwartek)

    z = ZyczeniaOgolne(start=wtorek, koniec=czwartek)
    assert z.relevant_zakres_dat(wtorek)
    assert z.relevant_zakres_dat(sroda)
    assert z.relevant_zakres_dat(czwartek)

    z = ZyczeniaOgolne(start=sroda, koniec=czwartek)
    assert not z.relevant_zakres_dat(wtorek)

    z = ZyczeniaOgolne(start=wtorek, koniec=sroda)
    assert not z.relevant_zakres_dat(piatek)


def test_ZyczeniaSzczegolowe_relevant_zakres_dat(nowy_rok, wtorek, sroda, czwartek):
    z = ZyczeniaSzczegolowe(miesiac_i_rok=nowy_rok, lista_dni="2,3")
    assert not z.relevant_zakres_dat(wtorek)
    assert z.relevant_zakres_dat(sroda)
    assert z.relevant_zakres_dat(czwartek)
