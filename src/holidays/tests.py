from datetime import date

import pytest

from .models import Holiday


@pytest.mark.django_db
def test_HolidayManager_from_workalendar():
    assert Holiday.objects.is_holiday(date(2019, 1, 1))


@pytest.mark.django_db
def test_HolidayManager_from_override():
    d = date(2019, 3, 4)

    assert not Holiday.objects.is_holiday(d)
    Holiday.objects.create(d)
    assert Holiday.objects.is_holiday(d)
