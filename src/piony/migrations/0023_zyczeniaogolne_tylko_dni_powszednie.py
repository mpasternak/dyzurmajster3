# Generated by Django 2.1.7 on 2019-03-23 02:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('piony', '0022_dostepnoscogolnapionu_tylko_dni_powszednie'),
    ]

    operations = [
        migrations.AddField(
            model_name='zyczeniaogolne',
            name='tylko_dni_powszednie',
            field=models.BooleanField(default=False),
        ),
    ]
