# Generated by Django 2.2 on 2019-07-30 10:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('objectives', '0018_auto_20190729_1012'),
    ]

    operations = [
        migrations.AddField(
            model_name='numberobjective',
            name='exceed_consecutive_count',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='numberobjective',
            name='exceed_flg',
            field=models.CharField(default='0', max_length=1),
        ),
    ]
