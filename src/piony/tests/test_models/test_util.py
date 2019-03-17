from datetime import date

import pytest
from django.core.exceptions import ValidationError

from piony.models.util import lista_dni, parsuj_liste_dni, sprawdz_liste_wobec_miesiaca, spacja_inicjal_z_kropka, \
    pracownik_etatowy


def test_lista_dni():
    with pytest.raises(ValidationError):
        lista_dni("1-32")

    with pytest.raises(ValidationError):
        lista_dni("dupa")

    with pytest.raises(ValidationError):
        lista_dni("-10")

    with pytest.raises(ValidationError):
        lista_dni("43,")

    with pytest.raises(ValidationError):
        lista_dni("0")

    with pytest.raises(ValidationError):
        lista_dni("32")

    lista_dni("1-31")
    lista_dni("1,2,3,4,5")
    lista_dni("1,2,3,4,5-10,12-31")

    with pytest.raises(ValidationError):
        lista_dni("1, 2, 3, 4, 32, 5")


def test_parsuj_liste_dni():
    assert list(parsuj_liste_dni("")) == []
    assert list(parsuj_liste_dni("1,2,3")) == [1, 2, 3]
    assert list(parsuj_liste_dni("1-100")) == [range(1, 101)]


def test_sprawdz_liste_wobec_miesiaca():
    with pytest.raises(ValidationError):
        sprawdz_liste_wobec_miesiaca("29", date(2019, 2, 1))
    sprawdz_liste_wobec_miesiaca("28", date(2019, 2, 1))


def test_sprawdz_liste_wobec_miesiaca_pusty_ciag():
    sprawdz_liste_wobec_miesiaca("", date(2019, 2, 1))


def test_spacja_inicjal_z_kropka():
    assert spacja_inicjal_z_kropka("Kowalski") == " K."
    assert spacja_inicjal_z_kropka("") == ""


def test_pracownik_etatowy(admin_user, pion):
    p = pracownik_etatowy(admin_user)
