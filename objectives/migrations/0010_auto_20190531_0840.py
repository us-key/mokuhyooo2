# Generated by Django 2.2 on 2019-05-31 08:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('objectives', '0009_auto_20190528_0848'),
    ]

    operations = [
        migrations.RenameField(
            model_name='numberobjective',
            old_name='year',
            new_name='iso_year',
        ),
        migrations.RenameField(
            model_name='numberobjectiveoutput',
            old_name='year',
            new_name='iso_year',
        ),
    ]