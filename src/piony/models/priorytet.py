from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from mptt.fields import TreeManyToManyField

from core.helpers import SprawdzZakresyMixin
from .pion import Pion
from .zyczenia import ZyczeniaPracownika


class Priorytet(models.Model):
    parent = models.ForeignKey(ZyczeniaPracownika, models.CASCADE)

    start = models.DateField(db_index=True)
    koniec = models.DateField(db_index=True)
    piony = TreeManyToManyField(Pion, related_name="+")
    priorytet = models.PositiveSmallIntegerField(default=50, validators=[
        MaxValueValidator(100),
        MinValueValidator(1)
    ])
    adnotacja = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = "priorytet"
        verbose_name_plural = "priorytety"

    def __str__(self):
        b = f"{self.parent.user}  ma priorytet {self.priorytet} {self.adnotacja or ''} od {self.start}"
        if self.koniec is not None:
            b += f" do {self.koniec}"
        return b
