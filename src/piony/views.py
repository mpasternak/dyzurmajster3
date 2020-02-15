from django.http import HttpResponseBadRequest
from django.views.generic import DetailView

from piony import const
from piony.forms import ParametryWydrukuForm
from piony.models import Wydruk, koniec_miesiaca, Grafik, poczatek_miesiaca, poczatek_tygodnia


class WydrukView(DetailView):
    slug_field = 'kod'
    slug_url_kwarg = 'kod'
    model = Wydruk

    def get_context_data(self, **kwargs):
        grafik = Grafik.objects.all().first()

        f = ParametryWydrukuForm(self.request.GET)
        if not f.is_valid():
            raise Exception("parametry niepoprawne")

        start = f.cleaned_data['start']
        if start is None:
            if self.object.rodzaj == const.TYGODNIOWY:
                start = poczatek_tygodnia(poczatek_miesiaca())
            elif self.object.rodzaj == const.MIESIECZNY:
                start = poczatek_miesiaca()
            else:
                raise Exception("Nieznany rodzaj wydruku %r" % self.object.rodzaj)

        koniec = f.cleaned_data['koniec']
        if koniec is None:
            koniec = koniec_miesiaca(start)

        kwargs['wydruk'] = self.object.drukuj(grafik, start, koniec)
        return kwargs

#     def get_object
# def wydruk(request, kod_wydruku):
#     # user = User.objects.get(username=username) if username else None
#     return HttpResponse(
#
#     )
