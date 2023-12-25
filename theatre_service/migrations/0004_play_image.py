# Generated by Django 5.0 on 2023-12-11 18:29

import theatre_service.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "theatre_service",
            "0003_alter_performance_options_alter_reservation_options_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="play",
            name="image",
            field=models.ImageField(
                null=True, upload_to=theatre_service.models.play_image_file_path
            ),
        ),
    ]
