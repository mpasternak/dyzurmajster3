from datetime import date

import pytest
from model_mommy import mommy

from piony.const import POZA_PRACA
from piony.models import Pion, dostepne_piony, PrzerwaWPracyPionu


@pytest.mark.django_db
def test_str():
    p = mommy.make(Pion, nazwa="LOL", rodzaj=None)
    assert "LOL" in str(p)


@pytest.mark.django_db
def test_str_rodzaj():
    p = mommy.make(Pion, nazwa="LOL", rodzaj=POZA_PRACA)
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


@pytest.mark.django_db
def test_dostepne_piony_domyslnie_niedostepny(pion_dzienny, sroda):
    pion_dzienny.domyslnie_dostepny = False
    pion_dzienny.save()

    r = list(dostepne_piony(dzien=sroda))

    pion, dostepny, przyczyna = r[0]
    assert not dostepny


@pytest.mark.django_db
def test_dostepne_piony_domyslnie_niedostepny(pion_dzienny, sroda):
    pion_dzienny.domyslnie_dostepny = False
    pion_dzienny.save()

    r = list(dostepne_piony(dzien=sroda))

    pion, dostepny, przyczyna = r[0]
    assert not dostepny


@pytest.mark.django_db
def test_dostepne_piony_tylko_dni_powszednie(pion_nocny, wtorek, sroda):
    r = list(dostepne_piony(dzien=wtorek))
    pion, dostepny, przyczyna = r[0]
    assert dostepny

    dpo = pion.dostepnoscogolnapionu_set.create(
        tylko_dni_powszednie=True
    )
    r = list(dostepne_piony(dzien=wtorek))
    pion, dostepny, przyczyna = r[0]
    assert not dostepny

    r = list(dostepne_piony(dzien=sroda))
    pion, dostepny, przyczyna = r[0]
    assert dostepny

    dpo.dzien_3 = False
    dpo.save()
    r = list(dostepne_piony(dzien=sroda))
    pion, dostepny, przyczyna = r[0]
    assert dostepny

    pion_nocny.domyslnie_dostepny = False
    pion_nocny.save()
    r = list(dostepne_piony(dzien=sroda))
    pion, dostepny, przyczyna = r[0]
    assert not dostepny
