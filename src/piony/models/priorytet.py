from adminsortable.models import SortableMixin
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from mptt.fields import TreeManyToManyField

from .pion import Pion
from .zyczenia import ZyczeniaPracownika


class Priorytet(SortableMixin, models.Model):
    parent = models.ForeignKey(ZyczeniaPracownika, models.CASCADE)

    start = models.DateField(db_index=True)
    koniec = models.DateField(db_index=True)
    piony = TreeManyToManyField(Pion, related_name="+")
    priorytet = models.PositiveSmallIntegerField(default=50, validators=[
        MaxValueValidator(100),
        MinValueValidator(1)
    ])
    adnotacja = models.CharField(max_length=100, blank=True, null=True)

    kolejnosc = models.PositiveSmallIntegerField(default=0, blank=False, null=False)

    class Meta:
        verbose_name = "priorytet"
        verbose_name_plural = "priorytety"
        ordering = ['kolejnosc', ]

    def __str__(self):
        b = f"{self.parent.user}  ma priorytet {self.priorytet} {self.adnotacja or ''} od {self.start} (nr {self.kolejnosc})"
        if self.koniec is not None:
            b += f" do {self.koniec}"
        return b
