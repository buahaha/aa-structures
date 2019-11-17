import logging
from time import sleep
import yaml
import datetime

import pytz
import dhooks_lite

from django.db import models, transaction
from django.core.validators import MinValueValidator, MaxValueValidator

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCorporationInfo
from esi.clients import esi_client_factory

from . import evelinks
from .managers import EveGroupManager, EveTypeManager, EveRegionManager,\
    EveConstellationManager, EveSolarSystemManager, NotificationEntityManager
from .utils import LoggerAddTag, DATETIME_FORMAT, make_logger_prefix


logger = LoggerAddTag(logging.getLogger(__name__), __package__)


class General(models.Model):
    """Meta model for global app permissions"""

    class Meta:
        managed = False                         
        default_permissions = ()
        permissions = ( 
            ('basic_access', 'Can access this app and view'),
            ('view_alliance_structures', 'Can view alliance structures'),
            ('view_all_structures', 'Can view all structures'),
            ('add_structure_owner', 'Can add new structure owner'), 
        )


class Webhook(models.Model):
    """A destination for forwarding notification alerts"""
    
    TYPE_DISCORD = 1

    TYPE_CHOICES = [
        (TYPE_DISCORD, 'Discord Webhook'),        
    ]
    
    name = models.CharField(
        max_length=64, 
        unique=True,
        help_text='short name to identify this webhook'
    )
    webhook_type = models.IntegerField(
        choices=TYPE_CHOICES,
        default=TYPE_DISCORD,        
        help_text='type of this webhook'
    )
    url = models.CharField(
        max_length=255,      
        unique=True,
        help_text='URL of this webhook, e.g. https://discordapp.com/api/webhooks/123456/abcdef'
    )
    notes = models.TextField(
        null=True, 
        default=None, 
        blank=True,        
        help_text='you can add notes about this webhook here if you want'
    )

    def __str__(self):
        return self.name


class Owner(models.Model):
    """corporation that owns structures"""

    # errors
    ERROR_NONE = 0
    ERROR_TOKEN_INVALID = 1
    ERROR_TOKEN_EXPIRED = 2
    ERROR_INSUFFICIENT_PERMISSIONS = 3    
    ERROR_NO_CHARACTER = 4
    ERROR_ESI_UNAVAILABLE = 5
    ERROR_OPERATION_MODE_MISMATCH = 6
    ERROR_UNKNOWN = 99

    ERRORS_LIST = [
        (ERROR_NONE, 'No error'),
        (ERROR_TOKEN_INVALID, 'Invalid token'),
        (ERROR_TOKEN_EXPIRED, 'Expired token'),
        (ERROR_INSUFFICIENT_PERMISSIONS, 'Insufficient permissions'),
        (ERROR_NO_CHARACTER, 'No character set for fetching alliance contacts'),
        (ERROR_ESI_UNAVAILABLE, 'ESI API is currently unavailable'),
        (ERROR_OPERATION_MODE_MISMATCH, 'Operaton mode does not match with current setting'),
        (ERROR_UNKNOWN, 'Unknown error'),
    ]

    corporation = models.OneToOneField(
        EveCorporationInfo, 
        primary_key=True, 
        on_delete=models.CASCADE,
        help_text='Corporation owning structures'
    )
    character = models.ForeignKey(
        CharacterOwnership,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        help_text='character used for syncing structures'
    )
    version_hash = models.CharField(
        max_length=32, 
        null=True, 
        default=None, 
        blank=True,
        help_text='hash to identify changes to structures'
    )
    last_sync = models.DateTimeField(
        null=True, 
        default=None, 
        blank=True,
        help_text='when the last sync happened'
    )
    last_error = models.IntegerField(
        choices=ERRORS_LIST, 
        default=ERROR_NONE,
        help_text='error that occurred at the last sync atttempt (if any)'
    )
    webhook = models.ForeignKey(
        Webhook, 
        on_delete=models.SET_DEFAULT,
        null=True, 
        default=None, 
        blank=True,
        help_text='Webhook used for sending structure notifications'
    )

    def __str__(self):
        return str(self.corporation.corporation_name)
    
    def send_notifications_to_webhook(self, force_sent = False):
        """Send notifications to configured webhook"""
        
        add_prefix = make_logger_prefix(str(self))   
        if self.webhook:
            q = self.notification_set

            if not force_sent:
                q = q.filter(is_sent__exact=False)
            
            q = q.select_related()

            if q.count() > 0:
                logger.info(add_prefix('Trying to send {} notifications'.format(
                    q.count()
                )))
                
                for notification in q:
                    notification.send_to_webhook()
                    sleep(1)
            else:
                logger.info(add_prefix('No new notifications to send'))
        
        else:
            logger.info(add_prefix('Discord webhook not configured - '
                + 'skipping sending notifications'))

    @classmethod
    def get_esi_scopes(cls) -> list:
        return [
            'esi-corporations.read_structures.v1',
            'esi-universe.read_structures.v1',
            'esi-characters.read_notifications.v1'
        ]


class EveRegion(models.Model):
    """region in Eve Online"""
    id = models.IntegerField(
        primary_key=True,
        validators=[MinValueValidator(0)],
        help_text='Eve Online region ID'
    )
    name = models.CharField(max_length=100)

    objects = EveRegionManager()

    def __str__(self):
        return self.name


class EveConstellation(models.Model):
    """constellation in Eve Online"""
    id = models.IntegerField(
        primary_key=True,
        validators=[MinValueValidator(0)],
        help_text='Eve Online region ID'
    )
    name = models.CharField(max_length=100)
    eve_region = models.ForeignKey(EveRegion, on_delete=models.CASCADE)

    objects = EveConstellationManager()

    def __str__(self):
        return self.name


class EveSolarSystem(models.Model):
    """solar system in Eve Online"""
    id = models.IntegerField(
        primary_key=True, 
        validators=[MinValueValidator(0)],
        help_text='Eve Online solar system ID'
    )
    name = models.CharField(max_length=100)
    eve_constellation = models.ForeignKey(
        EveConstellation, 
        on_delete=models.CASCADE
    )
    security_status = models.FloatField()

    objects = EveSolarSystemManager()

    def __str__(self):
        return self.name


class EveGroup(models.Model):
    """type in Eve Online"""
    id = models.IntegerField(
        primary_key=True,
        validators=[MinValueValidator(0)],
        help_text='Eve Online group ID'
    )
    name = models.CharField(max_length=100)

    objects = EveGroupManager()
    
    def __str__(self):
        return self.name


class EveType(models.Model):
    """type in Eve Online"""
    EVE_TYPE_ID_POCO = 2233

    id = models.IntegerField(
        primary_key=True,
        validators=[MinValueValidator(0)],
        help_text='Eve Online type ID'
    )
    name = models.CharField(max_length=100)
    eve_group = models.ForeignKey(EveGroup, on_delete=models.CASCADE)

    objects = EveTypeManager()
    
    def __str__(self):
        return self.name

    def icon_url(self, size=64):
        return evelinks.get_type_image_url(
            self.id,
            size
        )

    @property
    def is_poco(self):
        return id == self.EVE_TYPE_ID_POCO    


class Structure(models.Model):
    """structure of a corporation"""

    STATE_NA = 0
    STATE_ANCHOR_VULNERABLE = 1
    STATE_ANCHORING = 2
    STATE_ARMOR_REINFORCE = 3
    STATE_ARMOR_VULNERABLE = 4
    STATE_DEPLOY_VULNERABLE = 5
    STATE_FITTING_INVULNERABLE = 6
    STATE_HULL_REINFORCE = 7
    STATE_HULL_VULNERABLE = 8
    STATE_ONLINE_DEPRECATED = 9
    STATE_ONLINING_VULNERABLE = 10
    STATE_SHIELD_VULNERABLE = 11
    STATE_UNANCHORED = 12
    STATE_UNKNOWN = 13
        
    STATE_CHOICES = [
        (STATE_NA, 'N/A'),
        (STATE_ANCHOR_VULNERABLE, 'anchor_vulnerable'),
        (STATE_ANCHORING, 'anchoring'),
        (STATE_ARMOR_REINFORCE, 'armor_reinforce'),
        (STATE_ARMOR_VULNERABLE, 'armor_vulnerable'),
        (STATE_DEPLOY_VULNERABLE, 'deploy_vulnerable'),
        (STATE_FITTING_INVULNERABLE, 'fitting_invulnerable'),
        (STATE_HULL_REINFORCE, 'hull_reinforce'),
        (STATE_HULL_VULNERABLE, 'hull_vulnerable'),
        (STATE_ONLINE_DEPRECATED, 'online_deprecated'),
        (STATE_ONLINING_VULNERABLE, 'onlining_vulnerable'),
        (STATE_SHIELD_VULNERABLE, 'shield_vulnerable'),
        (STATE_UNANCHORED, 'unanchored'),
        (STATE_UNKNOWN, 'unknown'),
    ]

    id = models.BigIntegerField(
        primary_key=True,
        help_text='The Item ID of the structure'
    )
    owner = models.ForeignKey(
        Owner, 
        on_delete=models.CASCADE,
        help_text='Corporation that owns the structure'
    )
    eve_type = models.ForeignKey(
        EveType, 
        on_delete=models.CASCADE,
        help_text='type of the structure'
    )
    name = models.CharField(
        max_length=255,
        help_text='The full name of the structure'
    )
    eve_solar_system = models.ForeignKey(
        EveSolarSystem, 
        on_delete=models.CASCADE
    )
    position_x = models.FloatField(        
        help_text='x position of the structure in the solar system'
    )
    position_y = models.FloatField(        
        help_text='y position of the structure in the solar system'
    )
    position_z = models.FloatField(        
        help_text='z position of the structure in the solar system'
    )    
    fuel_expires = models.DateTimeField(
        null=True, 
        default=None, 
        blank=True,
        help_text='Date on which the structure will run out of fuel'
    )
    next_reinforce_hour = models.IntegerField(
        null=True, 
        default=None, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        help_text='The requested change to reinforce_hour that will take effect at the time shown by next_reinforce_apply'
    )
    next_reinforce_weekday = models.IntegerField(
        null=True, 
        default=None, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        help_text='The date and time when the structure’s newly requested reinforcement times (e.g. next_reinforce_hour and next_reinforce_day) will take effect'
    )    
    next_reinforce_apply = models.DateTimeField(
        null=True, 
        default=None, 
        blank=True,
        help_text='The requested change to reinforce_weekday that will take effect at the time shown by next_reinforce_apply'
    )
    profile_id = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text='The id of the ACL profile for this citadel'
    )
    reinforce_hour = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        help_text='The hour of day that determines the four hour window when the structure will randomly exit its reinforcement periods and become vulnerable to attack against its armor and/or hull. The structure will become vulnerable at a random time that is +/- 2 hours centered on the value of this property'
    )
    reinforce_weekday = models.IntegerField(
        null=True, 
        default=None, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        help_text='The day of the week when the structure exits its final reinforcement period and becomes vulnerable to attack against its hull. Monday is 0 and Sunday is 6'
    )
    state = models.IntegerField(
        choices=STATE_CHOICES,
        help_text='Current state of the structure'
    )    
    state_timer_start = models.DateTimeField(
        null=True, 
        default=None, 
        blank=True,
        help_text='Date at which the structure will move to it’s next state'
    )
    state_timer_end = models.DateTimeField(
        null=True, 
        default=None, 
        blank=True,
        help_text='Date at which the structure entered it’s current state'
    )
    unanchors_at = models.DateTimeField(
        null=True, 
        default=None, 
        blank=True,
        help_text='Date at which the structure will unanchor'
    )    
    last_updated = models.DateTimeField(
        help_text='date this structure was last updated from the EVE server'
    )

    @property
    def state_str(self):
        msg = [(x, y) for x, y in self.STATE_CHOICES if x == self.state]
        return msg[0][1] if len(msg) > 0 else 'Undefined'

    @property
    def is_low_power(self):
        return not self.fuel_expires

    @property
    def is_reinforced(self):
        return self.state in [
            self.STATE_ARMOR_REINFORCE, 
            self.STATE_HULL_REINFORCE
        ]

    def __str__(self):
        return '{} - {}'.format(self.eve_solar_system, self.name)

    @classmethod
    def get_matching_state(cls, state_name) -> int:
        """returns matching state for given state name"""
        match = cls.STATE_UNKNOWN
        for x in cls.STATE_CHOICES:
            if state_name == x[1]:
                match = x
                break
        
        return match[0]


class StructureService(models.Model):
    """service of a structure"""

    STATE_OFFLINE = 1
    STATE_ONLINE = 2
    
    STATE_CHOICES = [
        (STATE_OFFLINE, 'offline'),        
        (STATE_ONLINE, 'online'),        
    ]

    structure = models.ForeignKey(
        Structure, 
        on_delete=models.CASCADE,
        help_text='Structure this service is installed to'
    )
    name = models.CharField(
        max_length=64,
        help_text='Name of the service'
    )
    state = models.IntegerField(
        choices=STATE_CHOICES,
        help_text='Current state of this service'
    )

    class Meta:
        unique_together = (('structure', 'name'),)

    def __str__(self):
        return '{}-{}'.format(str(self.structure), self.name)

    @classmethod
    def get_matching_state(cls, state_name) -> int:
        """returns matching state for given state name"""
        match = cls.STATE_OFFLINE
        for x in cls.STATE_CHOICES:
            if state_name == x[1]:
                match = x
                break
        
        return match[0]


class NotificationEntity(models.Model):
    """An EVE entity used in notifications"""
    
    TYPE_CHARACTER = 1
    TYPE_CORPORATION = 2
    TYPE_ALLIANCE = 3
    TYPE_FACTION = 4
    TYPE_OTHER = 5

    TYPE_CHOICES = [
        (TYPE_CHARACTER, 'character'),
        (TYPE_CORPORATION, 'corporation'),
        (TYPE_ALLIANCE, 'alliance'),
        (TYPE_FACTION, 'faction'),
        (TYPE_OTHER, 'other'),
    ]
    
    id = models.IntegerField(
        primary_key=True, 
        validators=[MinValueValidator(0)]
    )
    entity_type = models.IntegerField(
        choices=TYPE_CHOICES
    )
    name = models.CharField(
        max_length=255,
        null=True, 
        default=None, 
        blank=True
    )

    objects = NotificationEntityManager()

    def __str__(self):
        return str(self.id)

    @classmethod
    def get_matching_entity_type(cls, type_name) -> int:
        """returns matching entity type for given state name"""
        match = None
        for x in cls.TYPE_CHOICES:
            if type_name == x[1]:
                match = x
                break
        if not match:
            raise ValueError('Invalid entity type')
        else:
            return match[0]


class Notification(models.Model):
    """An EVE Online notification about structures"""
    
    EMBED_COLOR_INFO = 0x5bc0de
    EMBED_COLOR_SUCCESS = 0x5cb85c
    EMBED_COLOR_WARNING = 0xf0ad4e
    EMBED_COLOR_DANGER = 0xd9534f
    
    TYPE_STRUCTURE_ANCHORING = 501
    TYPE_STRUCTURE_DESTROYED = 502
    TYPE_STRUCTURE_FUEL_ALERT = 503
    TYPE_STRUCTURE_LOST_ARMOR = 504
    TYPE_STRUCTURE_LOST_SHIELD = 505
    TYPE_STRUCTURE_ONLINE = 506
    TYPE_STRUCTURE_SERVICES_OFFLINE = 507
    TYPE_STRUCTURE_UNANCHORING = 508
    TYPE_STRUCTURE_UNDER_ATTACK = 509
    TYPE_STRUCTURE_WENT_HIGH_POWER = 510
    TYPE_STRUCTURE_WENT_LOW_POWER = 511  
    TYPE_STRUCTURE_REINFORCEMENT_CHANGED = 512
    TYPE_OWNERSHIP_TRANSFERRED = 513

    TYPE_CHOICES = [
        (TYPE_STRUCTURE_ANCHORING, 'StructureAnchoring'),
        (TYPE_STRUCTURE_DESTROYED, 'StructureDestroyed'),
        (TYPE_STRUCTURE_FUEL_ALERT, 'StructureFuelAlert'),
        (TYPE_STRUCTURE_LOST_ARMOR, 'StructureLostArmor'),
        (TYPE_STRUCTURE_LOST_SHIELD, 'StructureLostShields'),
        (TYPE_STRUCTURE_ONLINE, 'StructureOnline'),
        (TYPE_STRUCTURE_SERVICES_OFFLINE, 'StructureServicesOffline'),
        (TYPE_STRUCTURE_UNANCHORING, 'StructureUnanchoring'),
        (TYPE_STRUCTURE_UNDER_ATTACK, 'StructureUnderAttack'),
        (TYPE_STRUCTURE_WENT_HIGH_POWER, 'StructureWentHighPower'),
        (TYPE_STRUCTURE_WENT_LOW_POWER, 'StructureWentLowPower'),        
        (TYPE_STRUCTURE_REINFORCEMENT_CHANGED, 'StructuresReinforcementChanged'),
        (TYPE_OWNERSHIP_TRANSFERRED, 'OwnershipTransferred'),        
    ]

    notification_id = models.BigIntegerField(        
        validators=[MinValueValidator(0)]
    )
    owner = models.ForeignKey(
        Owner, 
        on_delete=models.CASCADE,
        help_text='Corporation that received this notification'
    )
    sender = models.ForeignKey(NotificationEntity, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    notification_type = models.IntegerField(
        choices=TYPE_CHOICES
    )
    text = models.TextField(        
        null=True, 
        default=None, 
        blank=True
    )
    is_read = models.BooleanField(
        null=True, 
        default=None, 
        blank=True
    )    
    is_sent = models.BooleanField(
        default=False,
        blank=True
    )
    last_updated = models.DateTimeField()

    class Meta:
        unique_together = (('notification_id', 'owner'),)

    def __str__(self):
        return str(self.notification_id)

    def _generate_embed(self) -> dhooks_lite.Embed:
        """generates a Discord embed for this notification"""
        def gen_solar_system_text(solar_system: EveSolarSystem) -> str:
            text = '[{}]({}) ({})'.format(
                solar_system.name,
                evelinks.get_entity_profile_url_by_name(
                    evelinks.ESI_CATEGORY_SOLARSYSTEM,
                    solar_system.name
                ),
                solar_system.eve_constellation.eve_region.name
            )
            return text

        def ldap_datetime_2_dt(ldap_dt: int) -> datetime:
            """converts ldap time to datatime"""    
            return pytz.utc.localize(datetime.datetime.utcfromtimestamp(
                (ldap_dt / 10000000) - 11644473600
            ))

        def ldap_timedelta_2_timedelta(ldap_td: int) -> datetime.timedelta:
            """converts a ldap timedelta into a dt timedelta"""
            return datetime.timedelta(microsecond=ldap_td / 10)

        def gen_alliance_link(alliance_name):
            return '[{}]({})'.format(
                alliance_name,
                evelinks.get_entity_profile_url_by_name(
                    evelinks.ESI_CATEGORY_ALLIANCE,
                    alliance_name
            ))
        
        def gen_corporation_link(corporation_name):
            return '[{}]({})'.format(
                corporation_name,
                evelinks.get_entity_profile_url_by_name(
                    evelinks.ESI_CATEGORY_CORPORATION,
                    corporation_name
            ))

        def get_attacker_name(self, parsed_text):
            """returns the attacker name from a parsed_text"""
            if "allianceName" in parsed_text:               
                name = gen_alliance_link(parsed_text['allianceName'])
            elif "corpName" in parsed_text:
                name = gen_corporation_link(parsed_text['corpName'])
            else:
                name = "(unknown)"

            return name

        parsed_text = yaml.safe_load(self.text)        
        
        if self.notification_type in [
            self.TYPE_STRUCTURE_FUEL_ALERT,
            self.TYPE_STRUCTURE_SERVICES_OFFLINE,
            self.TYPE_STRUCTURE_WENT_LOW_POWER,
            self.TYPE_STRUCTURE_WENT_HIGH_POWER,
            self.TYPE_STRUCTURE_UNANCHORING,
            self.TYPE_STRUCTURE_UNDER_ATTACK,
            self.TYPE_STRUCTURE_LOST_SHIELD,
            self.TYPE_STRUCTURE_LOST_ARMOR,
            self.TYPE_STRUCTURE_DESTROYED
        ]:
            structure = Structure.objects\
                .get(id=parsed_text['structureID'])

            thumbnail = dhooks_lite.Thumbnail(structure.eve_type.icon_url())

            description = 'The {} **{}** in {} '.format(
                structure.eve_type.name, 
                structure.name,
                gen_solar_system_text(structure.eve_solar_system)
            )

            if self.notification_type == self.TYPE_STRUCTURE_FUEL_ALERT:
                title = 'Structure fuel alert'
                description += 'has less then 24hrs fuel left.'
                color = self.EMBED_COLOR_DANGER

            elif self.notification_type == self.TYPE_STRUCTURE_SERVICES_OFFLINE:
                services_list = '\n'.join([
                    x.name 
                    for x in structure.structureservice_set.all().order_by('name')
                ])
                title = 'Structure services off-line'
                description += 'has all services off-lined:\n*{}*'.format(
                        services_list
                    )
                color = self.EMBED_COLOR_DANGER

            elif self.notification_type == self.TYPE_STRUCTURE_WENT_LOW_POWER:
                title = 'Structure low power'
                description += 'went to **low power** mode.'
                color = self.EMBED_COLOR_WARNING

            elif self.notification_type == self.TYPE_STRUCTURE_WENT_HIGH_POWER:
                title = 'Structure full power'
                description += 'went to **full power** mode.'
                color = self.EMBED_COLOR_SUCCESS

            elif self.notification_type == self.TYPE_STRUCTURE_UNANCHORING:
                title = 'Structure un-anchoring'            
                unanchored_at = self.timestamp \
                    + ldap_timedelta_2_timedelta(parsed_text['timeLeft'])
                description += 'has started un-anchoring. '\
                    + 'It will be fully un-anchored at {}'.format(unanchored_at)
                color = self.EMBED_COLOR_SUCCESS

            elif self.notification_type == self.TYPE_STRUCTURE_UNDER_ATTACK:
                title = 'Structure under attack'
                description = 'is under attack by {}.'.format(
                    get_attacker_name(parsed_text)
                )
                color = self.EMBED_COLOR_DANGER

            elif self.notification_type == self.TYPE_STRUCTURE_LOST_SHIELD:
                title = 'Structure lost shield'
                timer_ends_at = self.timestamp \
                    + ldap_timedelta_2_timedelta(parsed_text['timeLeft'])
                description = 'has lost its shields. Armor timer end at {}.'.format(
                    timer_ends_at
                )
                color = self.EMBED_COLOR_DANGER

            elif self.notification_type == self.TYPE_STRUCTURE_LOST_ARMOR:
                title = 'Structure lost armor'
                timer_ends_at = self.timestamp \
                    + ldap_timedelta_2_timedelta(parsed_text['timeLeft'])
                description = 'has lost its shields. Hull timer end at {}.'.format(
                    timer_ends_at
                )
                color = self.EMBED_COLOR_DANGER

            elif self.notification_type == self.TYPE_STRUCTURE_DESTROYED:
                title = 'Structure destroyed'
                description = 'has been destroyed.'
                color = self.EMBED_COLOR_DANGER

        else:
            if self.notification_type == self.TYPE_OWNERSHIP_TRANSFERRED:
                client = esi_client_factory()
                structure_type, _ = EveType.objects.get_or_create_esi(
                    parsed_text['structureTypeID'],
                    client
                )
                solar_system, _ = EveSolarSystem.objects.get_or_create_esi(
                    parsed_text['solarSystemID'],
                    client
                )
                description = 'The {} **{}** in {} '.format(
                    structure_type.name,
                    parsed_text['structureName'],
                    gen_solar_system_text(solar_system)
                )
                from_corporation, _ = \
                    NotificationEntity.objects.get_or_create_esi(
                        parsed_text['oldOwnerCorpID'],
                        client
                    )
                to_corporation, _ = \
                    NotificationEntity.objects.get_or_create_esi(
                        parsed_text['newOwnerCorpID'],
                        client
                    )
                character, _ = \
                    NotificationEntity.objects.get_or_create_esi(
                        parsed_text['charID'],
                        client
                    )
                description += 'has been transferred from {} to {} by {}.'\
                    .format(
                        gen_corporation_link(from_corporation.name),
                        gen_corporation_link(to_corporation.name),
                        character.name
                )
                title = 'Ownership transferred'
                color = self.EMBED_COLOR_INFO
                thumbnail = dhooks_lite.Thumbnail(structure_type.icon_url())
            
            else:
                raise NotImplementedError()
                
        return dhooks_lite.Embed(
            title=title,
            description=description,
            color=color,
            thumbnail=thumbnail,
            timestamp=self.timestamp
        )


    def send_to_webhook(self):
        """sends this notification to the configured webhook"""
        if self.owner.webhook:
            add_prefix = make_logger_prefix(
                'notification:{}'.format(self.notification_id)
            )            
            username = '{} Notification'.format(
                self.owner.corporation.corporation_ticker
            )
            avatar_url = self.owner.corporation.logo_url()

            hook = dhooks_lite.Webhook(
                self.owner.webhook.url, 
                username=username,
                avatar_url=avatar_url
            )                        
            with transaction.atomic():
                logger.info(add_prefix(
                    'Trying to sent notification to webhook: {}'.format(
                        self.owner.webhook
                )))                
                
                desc = self.text
                try:
                    embed = self._generate_embed()         
                except Exception as ex:
                    logger.warning(add_prefix(
                        'Failed to generate embed: {}'.format(ex)
                    ))
                    raise ex
                else:                                                
                    hook.execute(embeds=[embed])
                    self.is_sent = True
                    self.save()

    @classmethod
    def get_matching_notification_type(cls, type_name) -> int:
        """returns matching notification type for given name or None"""
        match = None
        for x in cls.TYPE_CHOICES:
            if type_name == x[1]:
                match = x
                break
        if match:
            return match[0]
        else:
            return None

