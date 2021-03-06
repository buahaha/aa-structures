# Generated by Django 2.2.5 on 2019-11-29 03:08

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("structures", "0003_auto_20191125_2157"),
    ]

    operations = [
        migrations.AlterField(
            model_name="structure",
            name="reinforce_hour",
            field=models.IntegerField(
                blank=True,
                default=None,
                help_text="The hour of day that determines the four hour window when the structure will randomly exit its reinforcement periods and become vulnerable to attack against its armor and/or hull. The structure will become vulnerable at a random time that is +/- 2 hours centered on the value of this property",
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(23),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="structure",
            name="state",
            field=models.IntegerField(
                blank=True,
                choices=[
                    (0, "N/A"),
                    (1, "anchor_vulnerable"),
                    (2, "anchoring"),
                    (3, "armor_reinforce"),
                    (4, "armor_vulnerable"),
                    (5, "deploy_vulnerable"),
                    (6, "fitting_invulnerable"),
                    (7, "hull_reinforce"),
                    (8, "hull_vulnerable"),
                    (9, "online_deprecated"),
                    (10, "onlining_vulnerable"),
                    (11, "shield_vulnerable"),
                    (12, "unanchored"),
                    (13, "unknown"),
                ],
                default=13,
                help_text="Current state of the structure",
            ),
        ),
    ]
