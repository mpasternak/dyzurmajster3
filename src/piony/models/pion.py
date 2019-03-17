from django.db import models
from django.db.models import F, Q
from mptt.fields import TreeForeignKey
from mptt.managers import TreeManager
from mptt.models import MPTTModel

from core.helpers import SprawdzZakresyMixin
from holidays.models import Holiday
from piony import const


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

    parent = TreeForeignKey(
        'self', null=True, blank=True, related_name='children', db_index=True,
        verbose_name="Pion nadrzędny", on_delete=models.CASCADE)

    priorytet = models.PositiveSmallIntegerField(default=5, db_index=True)
    sort = models.PositiveSmallIntegerField(default=0)

    objects = PatchedTreeManager()

    def __str__(self):
        m = {
            None: "żaden",
            const.DZIENNY: "☀",
            const.NOCNYSWIATECZNY: "☾",
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

    for pion in Pion.objects.filter(rodzaj__in=map[holiday]).order_by('-priorytet', 'nazwa'):
        try:
            pwp = PrzerwaWPracyPionu.objects.get(
                Q(parent=pion) & (
                        Q(start__range=(dzien, dzien)) |
                        Q(koniec__range=(dzien, dzien)) |
                        Q(start__lt=dzien, koniec__gt=dzien)
                )
            )
            yield (pion, False, pwp.przyczyna)

        except PrzerwaWPracyPionu.DoesNotExist:
            yield (pion, True, None)


class PrzerwaWPracyPionu(SprawdzZakresyMixin, models.Model):
    parent = models.ForeignKey(Pion, models.CASCADE)
    start = models.DateField()
    koniec = models.DateField()
    przyczyna = models.CharField(max_length=50, default='nie pracuje')

    class Meta:
        verbose_name = 'przerwa w pracy pionu'
        verbose_name_plural = 'przerwy w pracy pionu'
