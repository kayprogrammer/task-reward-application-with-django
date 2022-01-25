# Generated by Django 3.2.8 on 2022-01-13 17:08

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0014_auto_20220113_1801'),
    ]

    operations = [
        migrations.AddField(
            model_name='withdrawal',
            name='date_created',
            field=models.DateTimeField(default=datetime.datetime(2022, 1, 13, 17, 8, 41, 726020, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='task',
            name='task_expiry_date',
            field=models.DateField(default=datetime.datetime(2022, 1, 13, 17, 8, 41, 726020, tzinfo=utc), null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='task_expiry_time',
            field=models.TimeField(default=datetime.datetime(2022, 1, 13, 17, 8, 41, 726020, tzinfo=utc), null=True),
        ),
    ]