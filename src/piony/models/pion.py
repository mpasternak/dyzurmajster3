from django.db import models
from django.db.models import F, Q
from mptt.fields import TreeForeignKey
from mptt.managers import TreeManager
from mptt.models import MPTTModel

from core.helpers import SprawdzZakresyMixin
from holidays.models import Holiday
from piony import const
from .util import ModelZAdnotacjaMixin, DostepnoscOgolnaMixin


class PatchedTreeManager(TreeManager):
    # wszystkie leafnodes
    # https://stackoverflow.com/questions/10863194/django-and-mptt-get-only-leaf-nodes
    # https://github.com/django-mptt/django-mptt/issues/612
    def get_leafnodes(self):
        return self.filter(lft=F('rght') - 1)


class Pion(MPTTModel):
    rodzaj = models.IntegerField(
        null=True,
        default=None,
        db_index=True,
        choices=(
            (None, "żaden"),
            (const.DZIENNY, "dzienny"),
            (const.NOCNYSWIATECZNY, "nocny/świąteczny"),
            (const.POZA_PRACA, "poza pracą")
        ),
    )

    nazwa = models.CharField(max_length=50, unique=True, db_index=True)

    symbol = models.CharField(max_length=3, null=True, blank=True)

    domyslnie_dostepny = models.BooleanField(default=True)

    ilosc_godzin = models.PositiveSmallIntegerField(
        null=True, blank=True, default=None,
        help_text="Jeżeli jest to pion nocny (popołudniowy) np. żylaki od 15tej do 19tej, "
                  "wpisz tutaj przeciętną ilość godzin dla tego pionu. Jeżeli jest to zwykły, "
                  "pełny pion dyżurowy lub dzienny (16, 24, 8 godzin) to pozostaw to pole puste. "
    )

    parent = TreeForeignKey(
        'self', null=True, blank=True, related_name='children', db_index=True,
        verbose_name="Pion nadrzędny", on_delete=models.CASCADE)

    priorytet = models.PositiveSmallIntegerField(default=5, db_index=True)
    sort = models.PositiveSmallIntegerField(default=0)

    objects = PatchedTreeManager()

    def ile_godzin(self, dzien):
        if self.ilosc_godzin is not None:
            return self.ilosc_godzin

        holiday = Holiday.objects.is_holiday(dzien)

        if self.rodzaj == const.DZIENNY:
            if holiday:
                return 0
            return 8

        if self.rodzaj == const.NOCNYSWIATECZNY:
            if holiday:
                return 24
            return 16

        if self.rodzaj == const.POZA_PRACA:
            return 0

        raise ValueError(self.pion.rodzaj)

    def __str__(self):
        m = {
            None: "żaden",
            const.DZIENNY: "☀",
            const.NOCNYSWIATECZNY: "☾",
            const.POZA_PRACA: ""
        }
        ret = self.nazwa
        if self.rodzaj is not None:
            ret += " %s" % m[self.rodzaj]
        return ret

    class Meta:
        verbose_name_plural = "piony"
        ordering = ['sort']


def dostepne_piony(dzien):
    holiday = Holiday.objects.is_holiday(dzien)
    map = {
        True: [const.NOCNYSWIATECZNY],
        False: [const.DZIENNY, const.NOCNYSWIATECZNY]
    }

    for pion in Pion.objects.filter(rodzaj__in=map[holiday]).order_by('priorytet', 'nazwa'):
        try:
            pwp = PrzerwaWPracyPionu.objects.get(
                Q(parent=pion) & (
                        Q(start__range=(dzien, dzien)) |
                        Q(koniec__range=(dzien, dzien)) |
                        Q(start__lt=dzien, koniec__gt=dzien)
                )
            )
            yield (pion, False, pwp.przyczyna)
            continue

        except PrzerwaWPracyPionu.DoesNotExist:
            pass

        found = False

        for regula in pion.dostepnoscogolnapionu_set.all().order_by('-kolejnosc'):
            if regula.relevant(dzien):
                found = True
                break

        if found:
            yield (pion, regula.czy_dostepny(dzien), regula.adnotacja)
            continue

        yield (pion, pion.domyslnie_dostepny, None)


class DostepnoscOgolnaPionu(DostepnoscOgolnaMixin, ModelZAdnotacjaMixin):
    parent = models.ForeignKey(Pion, models.CASCADE)

    def relevant(self, dzien):
        return self.relevant_zakres_dat(dzien)

    class Meta:
        ordering = ['kolejnosc']
        verbose_name_plural = 'dostępności ogólne pionów'
        verbose_name = 'dostępność ogólna pionu'


class PrzerwaWPracyPionu(SprawdzZakresyMixin, models.Model):
    parent = models.ForeignKey(Pion, models.CASCADE)
    start = models.DateField()
    koniec = models.DateField()
    przyczyna = models.CharField(max_length=50, default='nie pracuje')

    class Meta:
        verbose_name = 'przerwa w pracy pionu'
        verbose_name_plural = 'przerwy w pracy pionu'

# class KolejnoscPracownikaWPionie(models.Model):
#     parent = models.ForeignKey(Pion, models.CASCADE)
#     pracownik = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)
#     kolejnosc = models.PositiveSmallIntegerField(default=0, blank=False, null=False)
#
#     class Meta:
#         ordering = ['kolejnosc',]
#         verbose_name = 'kolejność pracownika w pionie'
#         verbose_name_plural = 'kolejności pracowników w pionach'
