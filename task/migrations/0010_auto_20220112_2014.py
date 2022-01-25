# Generated by Django 3.2.8 on 2022-01-12 19:14

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0009_auto_20220112_2007'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pendingearnings',
            name='disapproved_earnings',
            field=models.DecimalField(blank=True, decimal_places=3, default='0', max_digits=7, null=True),
        ),
        migrations.AlterField(
            model_name='pendingearnings',
            name='pending_earnings',
            field=models.DecimalField(blank=True, decimal_places=3, default='0', max_digits=7, null=True),
        ),
        migrations.AlterField(
            model_name='pendingearnings',
            name='verified_earnings',
            field=models.DecimalField(blank=True, decimal_places=3, default='0', max_digits=7, null=True),
        ),
        migrations.AlterField(
            model_name='pendingearnings',
            name='withdrawn_earnings',
            field=models.DecimalField(blank=True, decimal_places=3, default='0', max_digits=7, null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='task_expiry_date',
            field=models.DateField(default=datetime.datetime(2022, 1, 12, 19, 14, 16, 155566, tzinfo=utc), null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='task_expiry_time',
            field=models.TimeField(default=datetime.datetime(2022, 1, 12, 19, 14, 16, 155566, tzinfo=utc), null=True),
        ),
    ]