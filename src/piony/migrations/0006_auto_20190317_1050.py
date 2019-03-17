# Generated by Django 2.1.7 on 2019-03-17 09:50

import django.core.validators
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('piony', '0005_auto_20190317_0038'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grafik',
            name='uuid',
            field=models.UUIDField(default=uuid.UUID('34839295-248f-4b5d-997c-a569b3f0bf01'), editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name='zyczeniapracownika',
            name='min_odpoczynek_po_ciaglej_pracy',
            field=models.PositiveIntegerField(default=11, validators=[django.core.validators.MaxValueValidator(24)], verbose_name='Czas bez pracy po godzinach ciągłej pracy'),
        ),
    ]