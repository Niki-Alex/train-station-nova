# Generated by Django 4.2.4 on 2023-08-29 17:40

import datetime
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("railway_station", "0004_alter_trip_departure_time"),
    ]

    operations = [
        migrations.AlterField(
            model_name="trip",
            name="departure_time",
            field=models.DateTimeField(
                validators=[
                    django.core.validators.MinValueValidator(
                        datetime.datetime(
                            2023,
                            8,
                            29,
                            17,
                            40,
                            28,
                            728523,
                            tzinfo=datetime.timezone.utc,
                        )
                    )
                ]
            ),
        ),
    ]
