import pytest
from model_mommy import mommy

from piony.models import Pion


@pytest.mark.django_db
def test_str():
    p = mommy.make(Pion, nazwa="LOL", rodzaj=None)
    assert "LOL" in str(p)
