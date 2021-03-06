# Generated by Django 2.1.7 on 2019-03-18 10:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('piony', '0015_auto_20190318_0616'),
    ]

    operations = [
        migrations.AddField(
            model_name='zyczeniapracownika',
            name='adnotacje',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='elementwydruku',
            name='rodzaj',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Dzień'), (2, 'Dzień tygodnia'), (3, 'Pion'), (4, 'Wolne'), (5, 'Nierozpisani'), (6, 'Pion dzienny'), (7, 'Pion dyżurowy')]),
        ),
        migrations.AlterField(
            model_name='wydruk',
            name='rodzaj',
            field=models.PositiveSmallIntegerField(choices=[(1, 'miesięczny'), (2, 'tygodniowy')]),
        ),
    ]
