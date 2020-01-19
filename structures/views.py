import calendar
import logging

from django.db import transaction
from django.http import HttpResponse, JsonResponse, HttpResponseServerError
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required, permission_required

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo, \
    EveAllianceInfo
from esi.decorators import token_required

from . import evelinks, tasks, __title__
from .app_settings import STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED
from .forms import TagsFilterForm
from .models import *
from .utils import messages_plus, DATETIME_FORMAT, notify_admins, LoggerAddTag


logger = LoggerAddTag(logging.getLogger(__name__), __package__)


STRUCTURE_LIST_ICON_RENDER_SIZE = 64
STRUCTURE_LIST_ICON_OUTPUT_SIZE = 32

QUERY_PARAM_TAGS = 'tags'

@login_required
@permission_required('structures.basic_access')
def index(request):       
    """main view showing the structure list"""
        
    tags = list()
    if request.method == 'POST':                    
        form = TagsFilterForm(data=request.POST)
        if form.is_valid():                        
            for name, activated in form.cleaned_data.items():
                if activated:
                    tags.append(name)

            url = reverse('structures:index')
            if tags:
                url += '?tags={}'.format(','.join(tags))
            return redirect(url)
    else:        
        tags_raw = request.GET.get(QUERY_PARAM_TAGS)
        if tags_raw:
            tags_parsed = tags_raw.split(',')
            tags = [
                x.name for x in StructureTag.objects.all().order_by('name') 
                if x.name in tags_parsed
            ]        
        
        form = TagsFilterForm(initial={x: True for x in tags})


    context = {
        'page_title': 'Alliance Structures',
        'tags': tags,
        'tags_filter_form': form
    }    
    return render(request, 'structures/index.html', context)


@login_required
@permission_required('structures.basic_access')
def structure_list_data(request):
    """returns structure list in JSON for AJAX call in index view"""    
    
    tags_raw = request.GET.get(QUERY_PARAM_TAGS)
    if tags_raw:
        tags = tags_raw.split(',')            
    else:
        tags = None
    
    if request.user.has_perm('structures.view_all_structures'):
        structures_query = Structure.objects.all().select_related()
        if tags:
            structures_query = structures_query\
                .filter(tags__name__in=tags)\
                .distinct()
    
    else:                
        
        corporation_ids = {
            character.character.corporation_id 
            for character in request.user.character_ownerships.all()
        }
        corporations = list(EveCorporationInfo.objects\
            .filter(corporation_id__in=corporation_ids)
        )
        if request.user.has_perm('structures.view_alliance_structures'):
            alliances = {
                corporation.alliance
                for corporation in corporations if corporation.alliance
            }
            for alliance in alliances:
                corporations += alliance.evecorporationinfo_set.all()            
            
            corporations = list(set(corporations))
            
        structures_query = Structure.objects\
            .filter(owner__corporation__in=corporations) \
            .select_related()

    structures_data = list()
    for structure in structures_query:        
        
        row = {
            'structure_id': structure.id,
            'is_poco': structure.eve_type.is_poco
        }
        
        # owner
        corporation = structure.owner.corporation
        if corporation.alliance:
            alliance_name = corporation.alliance.alliance_name            
        else: 
            alliance_name = ""            
                
        corporation_url = evelinks.get_entity_profile_url_by_name(
            evelinks.ESI_CATEGORY_CORPORATION,
            corporation.corporation_name
        )

        row['owner'] = '<a href="{}">{}</a><br>{}'.format(
            corporation_url,
            corporation.corporation_name,
            alliance_name
        )
        row['alliance_name'] = alliance_name
        row['corporation_name'] = corporation.corporation_name

        # corporation icon
        row['corporation_icon'] = '<img src="{}" width="{}" height="{}"/>'\
            .format(
                corporation.logo_url(size=STRUCTURE_LIST_ICON_RENDER_SIZE),
                STRUCTURE_LIST_ICON_OUTPUT_SIZE,
                STRUCTURE_LIST_ICON_OUTPUT_SIZE,
            )
        
        # location        
        row['solar_system_name'] = structure.eve_solar_system.name
        solar_system_url = evelinks.get_entity_profile_url_by_name(
            evelinks.ESI_CATEGORY_SOLARSYSTEM,
            row['solar_system_name']
        )
        row['region_name'] = structure.eve_solar_system.eve_constellation.eve_region.name
        row['location'] = '<a href="{}">{}</a><br>{}'.format(
            solar_system_url,
            structure.eve_solar_system.name,
            row['region_name']
        )        
        
        # type icon
        row['type_icon'] = '<img src="{}" width="{}" height="{}"/>'.format(
            structure.eve_type.icon_url(size=STRUCTURE_LIST_ICON_RENDER_SIZE),
            STRUCTURE_LIST_ICON_OUTPUT_SIZE,
            STRUCTURE_LIST_ICON_OUTPUT_SIZE,
        )        
        
        # type name              
        row['type_name'] = structure.eve_type.name
        row['type'] = row['type_name']

        # row name
        row['is_low_power'] = structure.is_low_power
        row['is_low_power_str'] = 'yes' if structure.is_low_power else 'no'
        row['structure_name'] = structure.name
        if structure.is_low_power:
            row['structure_name'] += '<br>[LOW POWER]'

        # services
        services = list()
        for service in structure.structureservice_set.all().order_by('name'):
            if service.state == StructureService.STATE_OFFLINE:
                service_name = '<del>{}</del>'. format(service.name)
            else:
                service_name = service.name
            services.append(service_name)
        row['services'] = '<br>'.join(services)
            
        # add reinforcement infos
        row['is_reinforced'] = structure.is_reinforced
        row['is_reinforced_str'] = 'yes' if structure.is_reinforced else 'no'
        if structure.reinforce_hour:
            reinforce_hour_str = str(structure.reinforce_hour) + ":00"
        else:
            reinforce_hour_str = ''
        
        if structure.reinforce_weekday:            
            reinforce_day_str = calendar.day_name[structure.reinforce_weekday]
        else:
            reinforce_day_str = ''
        
        if not row['is_poco']:
            row['reinforcement'] = '{}<br>{}'.format(
                reinforce_day_str,
                reinforce_hour_str
            )
        else:
            row['reinforcement'] = reinforce_hour_str

        # add date when fuel runs out
        if structure.state == Structure.STATE_UNKNOWN:
            row['fuel_expires'] = ''
        else:
            if structure.fuel_expires:
                row['fuel_expires'] = \
                    structure.fuel_expires.strftime(DATETIME_FORMAT)
            else:
                row['fuel_expires'] = 'N/A'
        
        # state
        if row['is_poco']:
            row['state_str'] = 'N/A'
            row['state_details'] = 'N/A'
            
        else:
            row['state_str'] = structure.state_str
            row['state_details'] = row['state_str']
            if structure.state_timer_end:
                row['state_details'] += '<br>{}'.format(                    
                    structure.state_timer_end.strftime(DATETIME_FORMAT)
                )

        structures_data.append(row)
       
    return JsonResponse(structures_data, safe=False)


@login_required
@permission_required('structures.add_structure_owner')
@token_required(scopes=Owner.get_esi_scopes())
def add_structure_owner(request, token):    
    token_char = EveCharacter.objects.get(character_id=token.character_id)
    
    success = True
    try:
        owned_char = CharacterOwnership.objects.get(
            user=request.user,
            character=token_char
        )        
    except CharacterOwnership.DoesNotExist:
        messages_plus.error(
            request,
            'You can only use your main or alt characters to add corporations.'
            + 'However, character <strong>{}</strong> is neither. '.format(
                token_char.character_name
            )
        )
        success = False
    
    if success:
        try:
            corporation = EveCorporationInfo.objects.get(
                corporation_id=token_char.corporation_id
            )
        except EveCorporationInfo.DoesNotExist:
            corporation = EveCorporationInfo.objects.create_corporation(
                token_char.corporation_id
            )            
        
        with transaction.atomic():
            owner, created = Owner.objects.update_or_create(
                corporation=corporation,
                defaults={
                    'character': owned_char
                }                    
            )
            default_webhooks = Webhook.objects.filter(is_default__exact=True)
            if default_webhooks:
                for webhook in default_webhooks:
                    owner.webhooks.add(webhook)
                owner.save()

        tasks.update_structures_for_owner.delay(            
            owner_pk=owner.pk,
            force_sync=True,
            user_pk=request.user.pk
        )        
        messages_plus.success(
            request,             
            '<strong>{}</strong> has been added '.format(owner)
            + 'with <strong>{}</strong> as sync character. '.format(
                    owner.character.character.character_name, 
                )                        
            + 'We have started fetching structures for this corporation. '
            + 'You will receive a reports once completed.'
        )
        if STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED:
            notify_admins(
                message='{} was added as new structure owner by {}.'.format(
                    owner.corporation.corporation_name,
                    request.user.username
                ), 
                title='{}: Structure owner added: {}'.format(
                    __title__,
                    owner.corporation.corporation_name
                )
            )
    return redirect('structures:index')


def service_status(request):
    """public view to 3rd party monitoring
    
    This is view allows running a 3rd party monitoring on the status 
    of this services. Service will be reported as down if any of the
    configured structure or notifications syncs fails or is delayed
    """
    ok = True
    for owner in Owner.objects.filter(
        is_included_in_service_status__exact=True
    ):
        ok = ok and owner.is_all_syncs_ok()
    
    if ok:
        return HttpResponse('service is up')
    else:
        return HttpResponseServerError('service is down')

