# Generated by Django 3.1.12 on 2021-07-19 14:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("structures", "0037_auto_20210719_1310"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fuelnotificationconfig",
            name="channel_ping_type",
            field=models.CharField(
                choices=[("NO", "none"), ("HE", "here"), ("EV", "everyone")],
                default="HE",
                help_text="Option to ping every member of the channel. This setting can be overruled by owner or webhook configuration",
                max_length=2,
                verbose_name="channel pings",
            ),
        ),
    ]