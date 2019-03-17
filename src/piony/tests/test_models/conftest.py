from datetime import date

import pytest

from piony import const
from piony.models import ZyczeniaPracownika, Pion, Grafik, Wpis


@pytest.fixture
def zp(admin_user):
    return ZyczeniaPracownika.objects.create(user=admin_user)


@pytest.fixture
@pytest.mark.django_db
def pion():
    return Pion.objects.create(nazwa="Hej")


@pytest.fixture
@pytest.mark.django_db
def pion_dzienny():
    return Pion.objects.create(nazwa="Dzienny", rodzaj=const.DZIENNY)


@pytest.fixture
@pytest.mark.django_db
def pion_nocny():
    return Pion.objects.create(nazwa="Nocny", rodzaj=const.NOCNYSWIATECZNY)


@pytest.fixture
def poniedzialek():
    return date(2018, 12, 31)


@pytest.fixture
def nowy_rok():
    return date(2019, 1, 1)


@pytest.fixture
def wtorek():
    return date(2019, 1, 1)


@pytest.fixture
def dzien_nastepny():
    return date(2019, 1, 2)


@pytest.fixture
def sroda():
    return date(2019, 1, 2)


@pytest.fixture
def czwartek():
    return date(2019, 1, 3)


@pytest.fixture
def piatek():
    return date(2019, 1, 4)


@pytest.fixture
def niedziela():
    return date(2019, 1, 6)


@pytest.fixture
def luty():
    return date(2019, 2, 1)


@pytest.fixture
def grafik(db, nowy_rok):
    return Grafik.objects.create(nazwa="Testowy")


@pytest.fixture
@pytest.mark.django_db
def wpis(grafik, pion, admin_user):
    return Wpis.objects.create(user=admin_user, grafik=grafik, pion=pion, dzien=date(2019, 1, 1))


