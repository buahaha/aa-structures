# Generated by Django 3.1.12 on 2021-07-19 13:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("structures", "0036_auto_20210719_1307"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fuelnotificationconfig",
            name="color",
            field=models.IntegerField(
                blank=True,
                choices=[
                    (14242639, "danger"),
                    (6013150, "info"),
                    (6076508, "success"),
                    (15773006, "warning"),
                ],
                default=15773006,
                null=True,
            ),
        ),
    ]