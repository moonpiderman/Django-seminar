# Generated by Django 3.1 on 2021-02-25 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seminar', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='seminar',
            name='time',
            field=models.TimeField(default='00:00'),
        ),
    ]
