from django.contrib.auth.models import User

from .dostepnosc import *
from .grafik import *
from .pion import *


class Pracownik(User):
    class Meta:
        proxy = True
        verbose_name_plural = "pracownicy"
