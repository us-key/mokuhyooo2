# Generated by Django 2.2 on 2019-04-30 00:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('objectives', '0004_numberobjectiveoutput_week_index'),
    ]

    operations = [
        migrations.AlterField(
            model_name='numberobjectivemaster',
            name='number_kind',
            field=models.CharField(choices=[('N', '数値'), ('P', '時間'), ('T', '時刻')], max_length=1),
        ),
        migrations.AlterField(
            model_name='numberobjectivemaster',
            name='summary_kind',
            field=models.CharField(choices=[('S', '合計'), ('A', '平均')], max_length=1),
        ),
    ]
