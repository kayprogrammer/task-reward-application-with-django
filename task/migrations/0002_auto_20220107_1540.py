# Generated by Django 3.2.8 on 2022-01-07 14:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='task_expiry_time',
            field=models.TimeField(default='02-40-24', null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(help_text='Email', max_length=40, null=True, unique=True, verbose_name='email address'),
        ),
    ]