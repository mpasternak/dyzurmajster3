# Generated by Django 2.1.7 on 2019-03-23 01:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('piony', '0021_auto_20190323_0250'),
    ]

    operations = [
        migrations.AddField(
            model_name='dostepnoscogolnapionu',
            name='tylko_dni_powszednie',
            field=models.BooleanField(default=False),
        ),
    ]