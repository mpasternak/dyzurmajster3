from datetime import date

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
