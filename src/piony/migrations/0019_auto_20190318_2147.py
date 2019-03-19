# Generated by Django 2.1.7 on 2019-03-18 20:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('piony', '0018_auto_20190318_1213'),
    ]

    operations = [
        migrations.AddField(
            model_name='wydruk',
            name='font_size',
            field=models.CharField(blank=True, max_length=5, null=True, verbose_name='Wielkość czcionki (pt)'),
        ),
        migrations.AlterField(
            model_name='elementwydruku',
            name='rodzaj',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Data'), (2, 'Dzień tygodnia'), (8, 'Dzień miesiąca'), (3, 'Pion'), (4, 'Wolne'), (5, 'Nierozpisani'), (6, 'Pion dzienny'), (7, 'Pion dyżurowy')]),
        ),
    ]
