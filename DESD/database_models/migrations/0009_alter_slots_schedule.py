# Generated by Django 5.0.1 on 2024-03-07 15:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database_models', '0008_rename_duration_durations_duration_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='slots',
            name='schedule',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database_models.schedules'),
        ),
    ]
