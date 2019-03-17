# -*- encoding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.db import models

from core.helpers import SprawdzZakresyMixin


class Urlop(SprawdzZakresyMixin, models.Model):
    parent = models.ForeignKey("piony.ZyczeniaPracownika", models.CASCADE)
    start = models.DateField()
    koniec = models.DateField()
    rodzaj = models.CharField(
        max_length=100,
        choices=[
            ("wypoczynkowy", "wypoczynkowy"),
            ("szkoleniowy", "szkoleniowy"),
            ("na żądanie", "na żądanie"),
            ("L4", "zwolnienie lekarskie"),
            ("opieka", "na opiekę"),
            ("inny", "inny"),
        ])

    def __str__(self):
        return f"Urlop dla {self.parent.user.username} od {self.start} do {self.koniec}"

    class Meta:
        verbose_name = 'urlop'
        verbose_name_plural = 'urlopy'
