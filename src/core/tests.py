from datetime import date

from core.admin_helpers import DyzurmajsterUserChoiceField
from core.helpers import daterange


def test_DyzurmajsterUserChoiceField(admin_user):
    x = DyzurmajsterUserChoiceField()
    assert x.label_from_instance(admin_user) is not None


def test_daterange():
    assert len(list(daterange(date(2019, 1, 1),
                              date(2019, 1, 31)))) == 31
