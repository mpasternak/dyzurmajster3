from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError

from piony.models.priorytet import Priorytet


@pytest.fixture
def priorytet(zp, pion, nowy_rok):
    prio = Priorytet.objects.create(
        parent=zp,
        start=nowy_rok,
        koniec=nowy_rok + timedelta(days=15),
        priorytet=25,
        adnotacja="Priorytet pionu - test"
    )
    prio.piony.add(pion)
    return prio


def test_Priorytet_max_min(priorytet):
    priorytet.priorytet = 0
    with pytest.raises(ValidationError):
        priorytet.full_clean()

    priorytet.priorytet = 101
    with pytest.raises(ValidationError):
        priorytet.full_clean()


def test_Priorytet_str(priorytet):
    assert str(priorytet) != None


def test_Priorytet_clean(priorytet, pion, zp):
    drugiPriorytet = Priorytet.objects.create(
        parent=zp,
        start=priorytet.start,
        koniec=priorytet.koniec,
        adnotacja="clean() nie powinno tego zapisać"
    )
    with pytest.raises(ValidationError):
        drugiPriorytet.full_clean()
