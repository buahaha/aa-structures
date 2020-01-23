# Generated by Django 2.2.8 on 2020-01-23 14:29

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import multiselectfield.db.fields
import structures.models


class Migration(migrations.Migration):

    dependencies = [
        ('structures', '0006_auto_20200120_0147'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.IntegerField(choices=[(401, 'MoonminingAutomaticFracture'), (402, 'MoonminingExtractionCancelled'), (403, 'MoonminingExtractionFinished'), (404, 'MoonminingExtractionStarted'), (405, 'MoonminingLaserFired'), (513, 'OwnershipTransferred'), (501, 'StructureAnchoring'), (502, 'StructureDestroyed'), (503, 'StructureFuelAlert'), (504, 'StructureLostArmor'), (505, 'StructureLostShields'), (506, 'StructureOnline'), (507, 'StructureServicesOffline'), (508, 'StructureUnanchoring'), (509, 'StructureUnderAttack'), (510, 'StructureWentHighPower'), (511, 'StructureWentLowPower'), (601, 'OrbitalAttacked'), (602, 'OrbitalReinforced')]),
        ),
        migrations.AlterField(
            model_name='webhook',
            name='notification_types',
            field=multiselectfield.db.fields.MultiSelectField(choices=[(401, 'MoonminingAutomaticFracture'), (402, 'MoonminingExtractionCancelled'), (403, 'MoonminingExtractionFinished'), (404, 'MoonminingExtractionStarted'), (405, 'MoonminingLaserFired'), (513, 'OwnershipTransferred'), (501, 'StructureAnchoring'), (502, 'StructureDestroyed'), (503, 'StructureFuelAlert'), (504, 'StructureLostArmor'), (505, 'StructureLostShields'), (506, 'StructureOnline'), (507, 'StructureServicesOffline'), (508, 'StructureUnanchoring'), (509, 'StructureUnderAttack'), (510, 'StructureWentHighPower'), (511, 'StructureWentLowPower'), (601, 'OrbitalAttacked'), (602, 'OrbitalReinforced')], default=structures.models.get_default_notification_types, help_text='only notifications which selected types are sent to this webhook', max_length=75),
        ),
        migrations.CreateModel(
            name='EvePlanet',
            fields=[
                ('id', models.IntegerField(help_text='Eve Online item ID', primary_key=True, serialize=False, validators=[django.core.validators.MinValueValidator(0)])),
                ('name', models.CharField(max_length=100)),
                ('position_x', models.FloatField(blank=True, default=None, help_text='x position of the structure in the solar system', null=True)),
                ('position_y', models.FloatField(blank=True, default=None, help_text='y position of the structure in the solar system', null=True)),
                ('position_z', models.FloatField(blank=True, default=None, help_text='z position of the structure in the solar system', null=True)),
                ('eve_solar_system', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='structures.EveSolarSystem')),
                ('eve_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='structures.EveType')),
            ],
        ),
    ]