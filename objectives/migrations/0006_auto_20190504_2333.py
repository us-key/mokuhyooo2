# Generated by Django 2.2 on 2019-05-04 23:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('objectives', '0005_auto_20190430_0033'),
    ]

    operations = [
        migrations.RenameField(
            model_name='numberobjectivemaster',
            old_name='user_id',
            new_name='user',
        ),
    ]
