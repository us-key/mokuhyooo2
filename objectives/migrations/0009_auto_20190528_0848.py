# Generated by Django 2.2 on 2019-05-28 08:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('objectives', '0008_auto_20190506_1614'),
    ]

    operations = [
        migrations.RenameField(
            model_name='numberobjective',
            old_name='master_id',
            new_name='master',
        ),
        migrations.RenameField(
            model_name='numberobjectiveoutput',
            old_name='master_id',
            new_name='master',
        ),
    ]