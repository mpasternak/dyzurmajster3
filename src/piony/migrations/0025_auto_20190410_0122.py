# Generated by Django 2.2 on 2019-04-09 23:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('piony', '0024_wolne_jako_pion'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='wolne',
            name='grafik',
        ),
        migrations.RemoveField(
            model_name='wolne',
            name='user',
        ),
        migrations.AlterField(
            model_name='elementwydruku',
            name='rodzaj',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Data'), (2, 'Dzień tygodnia'), (8, 'Dzień miesiąca'), (3, 'Pion'), (6, 'Pion dzienny'), (7, 'Pion dyżurowy')]),
        ),
        migrations.DeleteModel(
            name='Nierozpisany',
        ),
        migrations.DeleteModel(
            name='Wolne',
        ),
    ]
