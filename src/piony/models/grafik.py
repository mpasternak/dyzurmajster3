from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import SET_NULL
from django.template import Template, Context, TemplateSyntaxError

from piony.models import Pion


def spacja_inicjal_z_kropka(s):
    try:
        return " " + s[0] + "."
    except IndexError:
        return ""


class Default_Template:
    """Domyślny renderer dla wpisów: nazwisko + 1 litera imienia."""

    @classmethod
    def render(klass, wpis):
        """Wyrenderuj nazwisko i inicjał imienia"""
        return f"{wpis.user.last_name}{spacja_inicjal_z_kropka(wpis.user.first_name)}"


class Wpis_Template(models.Model):
    """Renderer dla wpisów, renderujący wg template."""
    nazwa = models.CharField(max_length=50, unique=True)
    template = models.TextField(default='{{user.last_name}} {{user.first_name|first|capfirst}}')

    def clean(self):
        try:
            t = Template(self.template).render(Context())
        except TemplateSyntaxError:
            raise ValidationError({"template": "To nie jest poprawna templatka Django"})

    def render(self, wpis):
        return Template(self.template).render(
            Context(dict(user=wpis.user, dzien=wpis.dzien, pion=wpis.pion)))

    def __str__(self):
        return self.nazwa


class RenderowalnyElementGrafikaMixin:
    template = None

    def render(self):
        if self.template is None:
            return Default_Template.render(self)
        return self.template.render(self)


class Wpis(RenderowalnyElementGrafikaMixin, models.Model):
    dzien = models.DateField(db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pion = models.ForeignKey(Pion, on_delete=models.CASCADE)
    template = models.ForeignKey(Wpis_Template, default=None, blank=True, null=True, on_delete=SET_NULL)

    class Meta:
        unique_together = [
            ('user', 'dzien', 'pion')
        ]
        verbose_name_plural = 'wpisy'

    def __str__(self):
        return f"{self.dzien} {self.pion} {self.user}"


