# Generated by Django 2.1.7 on 2019-03-18 11:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('piony', '0016_auto_20190318_1136'),
    ]

    operations = [
        migrations.CreateModel(
            name='KolejkaDoPionuDump',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dzien', models.DateField(db_index=True)),
                ('zmodyfikowano', models.DateTimeField(auto_now=True)),
                ('dump', models.TextField()),
                ('grafik', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='piony.Grafik')),
                ('pion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='piony.Pion')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
