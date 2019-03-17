from datetime import date

import pytest
from model_mommy import mommy

from piony.models import Pion, dostepne_piony, PrzerwaWPracyPionu


@pytest.mark.django_db
def test_str():
    p = mommy.make(Pion, nazwa="LOL", rodzaj=None)
    assert "LOL" in str(p)


@pytest.mark.django_db
def test_dostepne_piony(pion_dzienny, pion_nocny):
    r = list(dostepne_piony(dzien=date(2019, 1, 1)))
    assert (len(r)) == 1

    r = list(dostepne_piony(dzien=date(2019, 1, 2)))
    assert (len(r)) == 2


@pytest.mark.django_db
def test_dostepne_piony_przerwa(pion_dzienny, pion_nocny):
    PrzerwaWPracyPionu.objects.create(
        parent=pion_nocny,
        start=date(2019, 1, 1),
        koniec=date(2019, 1, 1)
    )
    r = list(dostepne_piony(dzien=date(2019, 1, 1)))

    pion, dostepny, przyczyna = r[0]
    assert not dostepny

