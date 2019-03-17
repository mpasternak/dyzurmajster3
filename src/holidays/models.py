from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from workalendar.europe import Poland

cal = Poland()


class HolidayManager(models.Manager):
    def is_holiday(self, date):
        if date.isoweekday() > 5:
            return True

        if not cal.is_working_day(date):
            return True

        try:
            self.get(date=date)
            return True
        except ObjectDoesNotExist:
            return False


class Holiday(models.Model):
    date = models.DateField()
    objects = HolidayManager()

    class Meta:
        verbose_name_plural = "święta"
        verbose_name = "święto"
