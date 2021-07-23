# Generated by Django 3.1.13 on 2021-07-23 18:27

import multiselectfield.db.fields

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("structures", "0028_migrate_owner_characters"),
    ]

    operations = [
        migrations.CreateModel(
            name="FuelAlertConfig",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "channel_ping_type",
                    models.CharField(
                        choices=[("NO", "none"), ("HE", "here"), ("EV", "everyone")],
                        default="HE",
                        help_text="Option to ping every member of the channel. This setting can be overruled by the respective owner or webhook configuration",
                        max_length=2,
                        verbose_name="channel pings",
                    ),
                ),
                (
                    "end",
                    models.PositiveIntegerField(
                        help_text="End of alerts in hours before fuel expires"
                    ),
                ),
                (
                    "repeat",
                    models.PositiveIntegerField(
                        help_text="Notifications will be repeated every x hours. Set to 0 for no repeats"
                    ),
                ),
                (
                    "color",
                    models.IntegerField(
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
                ("is_enabled", models.BooleanField(default=True)),
                (
                    "start",
                    models.PositiveIntegerField(
                        help_text="Start of alerts in hours before fuel expires"
                    ),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name="ownercharacter",
            name="last_used_at",
        ),
        migrations.AddField(
            model_name="ownercharacter",
            name="notifications_last_used_at",
            field=models.DateTimeField(
                db_index=True,
                default=None,
                editable=False,
                help_text="when this character was last used for syncing notifications",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="ownercharacter",
            name="structures_last_used_at",
            field=models.DateTimeField(
                db_index=True,
                default=None,
                editable=False,
                help_text="when this character was last used for syncing structures",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="webhook",
            name="notification_types",
            field=multiselectfield.db.fields.MultiSelectField(
                choices=[
                    ("StructureAnchoring", "Upwell structure anchoring"),
                    ("StructureOnline", "Upwell structure went online"),
                    (
                        "StructureServicesOffline",
                        "Upwell structure services went offline",
                    ),
                    ("StructureWentHighPower", "Upwell structure went high power"),
                    ("StructureWentLowPower", "Upwell structure went low power"),
                    ("StructureUnanchoring", "Upwell structure unanchoring"),
                    ("StructureFuelAlert", "Upwell structure fuel alert"),
                    ("StructureRefueledExtra", "Upwell structure refueled (extra)"),
                    ("StructureUnderAttack", "Upwell structure is under attack"),
                    ("StructureLostShields", "Upwell structure lost shields"),
                    ("StructureLostArmor", "Upwell structure lost armor"),
                    ("StructureDestroyed", "Upwell structure destroyed"),
                    (
                        "StructuresReinforcementChanged",
                        "Upwell structure reinforcement time changed",
                    ),
                    ("OwnershipTransferred", "Upwell structure ownership transferred"),
                    ("OrbitalAttacked", "Customs office attacked"),
                    ("OrbitalReinforced", "Customs office reinforced"),
                    ("TowerAlertMsg", "Starbase attacked"),
                    ("TowerResourceAlertMsg", "Starbase fuel alert"),
                    ("TowerRefueledExtra", "Starbase refueled (extra)"),
                    ("MoonminingExtractionStarted", "Moonmining extraction started"),
                    ("MoonminingLaserFired", "Moonmining laser fired"),
                    (
                        "MoonminingExtractionCancelled",
                        "Moonmining extraction cancelled",
                    ),
                    ("MoonminingExtractionFinished", "Moonmining extraction finished"),
                    (
                        "MoonminingAutomaticFracture",
                        "Moonmining automatic fracture triggered",
                    ),
                    ("SovStructureReinforced", "Sovereignty structure reinforced"),
                    ("SovStructureDestroyed", "Sovereignty structure destroyed"),
                    ("EntosisCaptureStarted", "Sovereignty entosis capture started"),
                    (
                        "SovCommandNodeEventStarted",
                        "Sovereignty command node event started",
                    ),
                    ("SovAllClaimAquiredMsg", "Sovereignty claim acknowledgment"),
                    ("SovAllClaimLostMsg", "Sovereignty lost"),
                    ("WarDeclared", "War declared"),
                    ("AllyJoinedWarAggressorMsg", "War ally joined aggressor"),
                    ("AllyJoinedWarAllyMsg", "War ally joined ally"),
                    ("AllyJoinedWarDefenderMsg", "War ally joined defender"),
                    ("WarAdopted", "War adopted"),
                    ("WarInherited", "War inherited"),
                    ("CorpWarSurrenderMsg", "War party surrendered"),
                    ("WarRetractedByConcord", "War retracted by Concord"),
                    ("CorpBecameWarEligible", "War corporation became eligable"),
                    ("CorpNoLongerWarEligible", "War corporation no longer eligable"),
                    ("CorpAppNewMsg", "Character submitted application"),
                    ("CorpAppInvitedMsg", "Character invited to join corporation"),
                    ("CorpAppRejectCustomMsg", "Corp application rejected"),
                    ("CharAppWithdrawMsg", "Character withdrew application"),
                    ("CharAppAcceptMsg", "Character joins corporation"),
                    ("CharLeftCorpMsg", "Character leaves corporation"),
                ],
                default=[
                    "StructureAnchoring",
                    "StructureDestroyed",
                    "StructureFuelAlert",
                    "StructureRefueledExtra",
                    "StructureLostArmor",
                    "StructureLostShields",
                    "StructureOnline",
                    "StructureServicesOffline",
                    "StructureUnderAttack",
                    "StructureWentHighPower",
                    "StructureWentLowPower",
                    "OrbitalAttacked",
                    "OrbitalReinforced",
                    "TowerAlertMsg",
                    "TowerResourceAlertMsg",
                    "TowerRefueledExtra",
                    "SovStructureReinforced",
                    "SovStructureDestroyed",
                ],
                help_text="select which type of notifications should be forwarded to this webhook",
                max_length=962,
            ),
        ),
        migrations.AlterField(
            model_name="webhook",
            name="ping_groups",
            field=models.ManyToManyField(
                blank=True,
                default=None,
                help_text="Groups to be pinged for each notification - ",
                related_name="_webhook_ping_groups_+",
                to="auth.Group",
            ),
        ),
        migrations.CreateModel(
            name="FuelAlert",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "hours",
                    models.PositiveIntegerField(
                        db_index=True,
                        help_text="number of hours before fuel expiration this alert was sent",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "config",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="fuel_alerts",
                        to="structures.fuelalertconfig",
                    ),
                ),
                (
                    "structure",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="fuel_alerts",
                        to="structures.structure",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="fuelalert",
            constraint=models.UniqueConstraint(
                fields=("structure", "config", "hours"), name="functional_pk_fuelalert"
            ),
        ),
    ]
