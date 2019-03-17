from django.core.management import BaseCommand
from django.core.management import BaseCommand
from django.db import transaction

from piony.models import Grafik


class Command(BaseCommand):
    def add_arguments(self, parser):
        from piony.utils import parse_date
        parser.add_argument('start', type=parse_date)
        parser.add_argument('koniec', type=parse_date)

    @transaction.atomic
    def handle(self, start, koniec, *args, **options):
        grafik = Grafik.objects.all().first()

        grafik.wpis_set.filter(
            dzien__gte=start,
            dzien__lte=koniec
        ).delete()

        grafik.uloz(start, koniec)
