# Generated by Django 3.1.6 on 2021-04-29 12:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("eveonline", "0014_auto_20210105_1413"),
        ("authentication", "0017_remove_fleetup_permission"),
        ("structures", "0023_structure_fittings"),
    ]

    operations = [
        migrations.AddField(
            model_name="structure",
            name="has_core",
            field=models.BooleanField(
                blank=True,
                default=None,
                help_text="bool indicating if the structure has a quantum core",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="eveconstellation",
            name="eve_region",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="eve_constellations",
                to="structures.everegion",
            ),
        ),
        migrations.AlterField(
            model_name="evegroup",
            name="eve_category",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_DEFAULT,
                related_name="eve_groups",
                to="structures.evecategory",
            ),
        ),
        migrations.AlterField(
            model_name="evemoon",
            name="eve_solar_system",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="eve_moons",
                to="structures.evesolarsystem",
            ),
        ),
        migrations.AlterField(
            model_name="eveplanet",
            name="eve_solar_system",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="eve_planets",
                to="structures.evesolarsystem",
            ),
        ),
        migrations.AlterField(
            model_name="evesolarsystem",
            name="eve_constellation",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="eve_solar_systems",
                to="structures.eveconstellation",
            ),
        ),
        migrations.AlterField(
            model_name="evetype",
            name="eve_group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="eve_types",
                to="structures.evegroup",
            ),
        ),
        migrations.AlterField(
            model_name="notification",
            name="owner",
            field=models.ForeignKey(
                help_text="Corporation that received this notification",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="notifications",
                to="structures.owner",
            ),
        ),
        migrations.AlterField(
            model_name="owner",
            name="character",
            field=models.ForeignKey(
                blank=True,
                default=None,
                help_text="character used for syncing structures",
                null=True,
                on_delete=django.db.models.deletion.SET_DEFAULT,
                related_name="+",
                to="authentication.characterownership",
            ),
        ),
        migrations.AlterField(
            model_name="owner",
            name="corporation",
            field=models.OneToOneField(
                help_text="Corporation owning structures",
                on_delete=django.db.models.deletion.CASCADE,
                primary_key=True,
                related_name="structure_owners",
                serialize=False,
                to="eveonline.evecorporationinfo",
            ),
        ),
        migrations.AlterField(
            model_name="ownerasset",
            name="location_id",
            field=models.BigIntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name="ownerasset",
            name="owner",
            field=models.ForeignKey(
                help_text="Corporation that owns the assets",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="assets",
                to="structures.owner",
            ),
        ),
        migrations.AlterField(
            model_name="structure",
            name="owner",
            field=models.ForeignKey(
                help_text="Corporation that owns the structure",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="structures",
                to="structures.owner",
            ),
        ),
        migrations.AlterField(
            model_name="structureservice",
            name="structure",
            field=models.ForeignKey(
                help_text="Structure this service is installed to",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="services",
                to="structures.structure",
            ),
        ),
    ]
