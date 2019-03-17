# Generated by Django 2.1.7 on 2019-03-17 11:48

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('piony', '0004_auto_20190317_0024_squashed_0008_auto_20190317_1050'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='zyczeniaogolne',
            options={'ordering': ['kolejnosc'], 'verbose_name': 'życzenie ogólne', 'verbose_name_plural': 'życzenia ogólne'},
        ),
        migrations.AddField(
            model_name='zyczeniaogolne',
            name='kolejnosc',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='grafik',
            name='uuid',
            field=models.UUIDField(default=uuid.UUID('89168678-5a38-4bb2-9e5a-f7cbed539521'), editable=False, unique=True),
        ),
    ]
