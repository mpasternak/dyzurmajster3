from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db.models import Q


class SprawdzZakresyMixin:
    def clean(self):
        qry = self.__class__.objects.filter(
            Q(parent=self.parent) & (
                    Q(start__range=(self.start, self.koniec)) |
                    Q(koniec__range=(self.start, self.koniec)) |
                    Q(start__lt=self.start, koniec__gt=self.koniec)
            )
        )

        if self.pk:
            qry = qry.exclude(pk=self.pk)

        if qry.exists():
            raise ValidationError("Istnieje zachodzący zakres czasu dla tego użytkownika")


def daterange(start_date, end_date):
    for n in range(0, int((end_date - start_date).days + 1)):
        yield start_date + timedelta(days=n)
