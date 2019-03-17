# Generated by Django 2.1.7 on 2019-03-16 23:24

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('piony', '0003_auto_20190316_2246'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='grafik',
            name='parent',
        ),
        migrations.AddField(
            model_name='zyczeniapracownika',
            name='maks_dyzury',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True, verbose_name='Maks. dyżurów'),
        ),
        migrations.AlterField(
            model_name='grafik',
            name='uuid',
            field=models.UUIDField(default=uuid.UUID('8e74cf8c-99e8-40c1-b79a-f6653225b2f2'), editable=False, unique=True),
        ),
    ]
