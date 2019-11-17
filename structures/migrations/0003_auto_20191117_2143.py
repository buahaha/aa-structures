# Generated by Django 2.2.5 on 2019-11-17 21:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('structures', '0002_auto_20191117_1346'),
    ]

    operations = [
        migrations.AddField(
            model_name='webhook',
            name='is_default',
            field=models.BooleanField(default=False, help_text='default webhook for all newly added owners'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.IntegerField(choices=[(501, 'StructureAnchoring'), (502, 'StructureDestroyed'), (503, 'StructureFuelAlert'), (504, 'StructureLostArmor'), (505, 'StructureLostShields'), (506, 'StructureOnline'), (507, 'StructureServicesOffline'), (508, 'StructureUnanchoring'), (509, 'StructureUnderAttack'), (510, 'StructureWentHighPower'), (511, 'StructureWentLowPower'), (513, 'OwnershipTransferred')]),
        ),
    ]
