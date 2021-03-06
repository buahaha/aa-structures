# Generated by Django 3.1.6 on 2021-02-14 00:34

import multiselectfield.db.fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("structures", "0015_refactor_notification_types"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="notification_type",
            field=models.IntegerField(
                choices=[
                    (201, "CharAppAcceptMsg"),
                    (202, "CharLeftCorpMsg"),
                    (401, "MoonminingAutomaticFracture"),
                    (402, "MoonminingExtractionCancelled"),
                    (403, "MoonminingExtractionFinished"),
                    (404, "MoonminingExtractionStarted"),
                    (405, "MoonminingLaserFired"),
                    (501, "StructureAnchoring"),
                    (502, "StructureDestroyed"),
                    (503, "StructureFuelAlert"),
                    (504, "StructureLostArmor"),
                    (505, "StructureLostShields"),
                    (506, "StructureOnline"),
                    (507, "StructureServicesOffline"),
                    (508, "StructureUnanchoring"),
                    (509, "StructureUnderAttack"),
                    (510, "StructureWentHighPower"),
                    (511, "StructureWentLowPower"),
                    (513, "OwnershipTransferred"),
                    (601, "OrbitalAttacked"),
                    (602, "OrbitalReinforced"),
                    (701, "TowerAlertMsg"),
                    (702, "TowerResourceAlertMsg"),
                    (801, "EntosisCaptureStarted"),
                    (802, "SovCommandNodeEventStarted"),
                    (803, "SovAllClaimAquiredMsg"),
                    (804, "SovStructureReinforced"),
                    (805, "SovStructureDestroyed"),
                ]
            ),
        ),
        migrations.AlterField(
            model_name="webhook",
            name="notification_types",
            field=multiselectfield.db.fields.MultiSelectField(
                choices=[
                    (201, "CharAppAcceptMsg"),
                    (202, "CharLeftCorpMsg"),
                    (401, "MoonminingAutomaticFracture"),
                    (402, "MoonminingExtractionCancelled"),
                    (403, "MoonminingExtractionFinished"),
                    (404, "MoonminingExtractionStarted"),
                    (405, "MoonminingLaserFired"),
                    (501, "StructureAnchoring"),
                    (502, "StructureDestroyed"),
                    (503, "StructureFuelAlert"),
                    (504, "StructureLostArmor"),
                    (505, "StructureLostShields"),
                    (506, "StructureOnline"),
                    (507, "StructureServicesOffline"),
                    (508, "StructureUnanchoring"),
                    (509, "StructureUnderAttack"),
                    (510, "StructureWentHighPower"),
                    (511, "StructureWentLowPower"),
                    (513, "OwnershipTransferred"),
                    (601, "OrbitalAttacked"),
                    (602, "OrbitalReinforced"),
                    (701, "TowerAlertMsg"),
                    (702, "TowerResourceAlertMsg"),
                    (801, "EntosisCaptureStarted"),
                    (802, "SovCommandNodeEventStarted"),
                    (803, "SovAllClaimAquiredMsg"),
                    (804, "SovStructureReinforced"),
                    (805, "SovStructureDestroyed"),
                ],
                default=[
                    513,
                    509,
                    510,
                    401,
                    402,
                    403,
                    404,
                    405,
                    601,
                    602,
                    801,
                    802,
                    803,
                    804,
                    805,
                    501,
                    502,
                    503,
                    504,
                    505,
                    506,
                    507,
                    508,
                    701,
                    702,
                    511,
                ],
                help_text="only notifications which selected types are sent to this webhook",
                max_length=111,
            ),
        ),
    ]
