from datetime import timedelta, datetime

from django.core.management import BaseCommand
from django.db import transaction

from piony.models import Wpis, DostepnoscPionu


class Command(BaseCommand):
    def add_arguments(self, parser):
        from piony.utils import parse_date
        parser.add_argument('start', type=parse_date)
        parser.add_argument('koniec', type=parse_date)

    @transaction.atomic
    def handle(self, start, koniec, *args, **options):

        header = ["Data",
                  "Sala A",
                  "Sala B",
                  "Sala C",
                  "Sala D",
                  "Endo-U",
                  "Laryngologia",
                  "Endoskopie",
                  "Lekarz OIT",
                  "Dyżurny OIT",
                  "Dyżurny ANEST",
                  "Biernackiego dzień",
                  "Biernackiego dyżur",
                  "Nierozpisany",
                  "Po dyżurze",
                  "Urlop",
                  "L4",
                  "Żylaki",
                  ]


        def tabela(start, koniec):
            dane = {
                "tytul": "Rozkład prac na salach: %s - %s" % (start, koniec),
                "dane": []
            }
            for dzien in daterange(start, koniec):
                row = []
                for elem in header:
                    if elem == "Data":
                        row.append(dzien)

                    else:
                        try:
                            row.append("<br>".join([w.render() for w in Wpis.objects.filter(dzien=dzien, pion__nazwa=elem)]))

                        except Wpis.DoesNotExist:

                            # Nie ma wpisu na ten dzień - ale czy ten pion tego dnia w ogóle jest "czynny"?
                            value = ""
                            for elem in DostepnoscPionu.objects.filter(pion__nazwa=elem).order_by("-kolejnosc"):
                                if elem.relevant(dzien):
                                    value = f"<b>{elem.adnotacja}</b>"
                                    break

                            row.append(value)
                dane["dane"].append(row)
            return dane

        results = []
        if start.weekday() in [5, 6]:
            start += timedelta(days=7-start.weekday())
        start = start - timedelta(days=start.weekday())
        while start < koniec:
            results.append(
                tabela(start, start + timedelta(days=5))
            )
            start += timedelta(days=7)

        print("<head><meta charset=utf-8></head><body><style>* { font-family: 'Calibri'; font-size: 15pt; } th { background: #eeeeee; color:black; } @media print { .nextPage {page-break-before:always;}} </style>")
        for tabela in results:
            print(f"<center><h3>{tabela['tytul']}</h3></center>")
            print("<table border=1 bordercolor=black cellpadding=3 cellspacing=0>")
            for n_row in range(len(header)):
                print("<tr>")
                for elem in range(6):
                    if elem == 0:
                        print(f"<th valign=top align=right class=firstCol><b>{header[n_row]}</b></th>")
                    else:
                        if n_row == 0:
                            print(f"<th valign=top>{tabela['dane'][elem-1][n_row]}</th>")
                        else:
                            print(f"<td valign=top>{tabela['dane'][elem-1][n_row]}</td>")
                print("</tr>")
            print("</table>")
            print("<small>wygenerowane %s</small>" % datetime.now())
            print("<div class=nextPage>")
        print("</body>")
