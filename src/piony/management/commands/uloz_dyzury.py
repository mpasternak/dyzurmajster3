import dateutil.parser
from django.core.management import BaseCommand
from django.db import transaction

from piony.core import uloz_dyzury
from piony.models import Wpis



class Command(BaseCommand):
    def add_arguments(self, parser):
        from piony.utils import parse_date
        parser.add_argument('start', type=parse_date)
        parser.add_argument('koniec', type=parse_date)

    @transaction.atomic
    def handle(self, start, koniec, *args, **options):
        Wpis.objects.filter(dzien__gte=start, dzien__lte=koniec).delete()
        uloz_dyzury(start, koniec)
