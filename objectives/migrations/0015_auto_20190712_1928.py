# Generated by Django 2.2 on 2019-07-12 19:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('objectives', '0014_auto_20190627_0540'),
    ]

    operations = [
        migrations.AddField(
            model_name='numberobjectiveoutput',
            name='day_of_week',
            field=models.PositiveSmallIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='numberobjective',
            name='objective_value',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='numberobjectiveoutput',
            name='output_value',
            field=models.PositiveIntegerField(),
        ),
    ]