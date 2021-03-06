# Generated by Django 2.1.7 on 2019-03-16 21:46

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('piony', '0001_squashed_0003_auto_20190316_2217'),
    ]

    operations = [
        migrations.AddField(
            model_name='zyczeniapracownika',
            name='maks_dniowki_w_tygodniu',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True, verbose_name='Maks. dniówek w tygodniu'),
        ),
        migrations.AlterField(
            model_name='grafik',
            name='uuid',
            field=models.UUIDField(default=uuid.UUID('a6aede4a-9ca1-413e-9fe6-53b3ef65dbab'), editable=False, unique=True),
        ),
    ]
