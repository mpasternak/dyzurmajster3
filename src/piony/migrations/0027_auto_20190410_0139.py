# Generated by Django 2.2 on 2019-04-09 23:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('piony', '0026_auto_20190410_0131'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pion',
            name='symbol',
            field=models.CharField(blank=True, max_length=3, null=True),
        ),
    ]
