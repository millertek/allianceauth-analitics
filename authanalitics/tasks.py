import logging
import requests
import datetime
import csv

from celery import shared_task

from .models import AACharacter, AAzKillMonth
from allianceauth.corputils.models import CorpStats, CorpMember
from allianceauth.eveonline.models import EveCorporationInfo, EveCharacter
from django.utils.dateparse import parse_datetime
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from time import sleep

logger = logging.getLogger(__name__)

@shared_task
def update_character_stats(character_id):
    #logger.info('update_character_stats for %s starting' % str(character_id))
    # https://zkillboard.com/api/stats/characterID/####/
    _stats_request = requests.get("https://zkillboard.com/api/stats/characterID/" + str(character_id) + "/")
    _stats_json = _stats_request.json()
    sleep(1)

    # https://zkillboard.com/api/characterID/####/kills/
    _kills_request = requests.get("https://zkillboard.com/api/characterID/" + str(character_id) + "/kills/")
    _kills_json = _kills_request.json()
    sleep(1)

    _last_kill_date = None
    if len(_kills_json) > 0:
        # https://esi.evetech.net/latest/killmails/ID####/HASH####/?datasource=tranquility
        try:
            _last_kill_request = requests.get(
                "https://esi.evetech.net/latest/killmails/" + str(_kills_json[0]['killmail_id']) + "/" +
                str(_kills_json[0]['zkb']['hash']) + "/?datasource=tranquility")
            _last_kill_json = _last_kill_request.json()
            sleep(1)
            _last_kill_date = parse_datetime(_last_kill_json['killmail_time'])
        except:
            pass

    char_model, created = AACharacter.objects.update_or_create(character = EveCharacter.objects.get(character_id=int(character_id)))
    if created:
        pass
    

    if len(_stats_json.get('months', [])) > 0:
        for key, month in _stats_json.get('months', []).items():
            zkill_month, created = AAzKillMonth.objects.get_or_create(char=char_model, year=month.get('year', 0), month=month.get('month', 0))
            if created:
                pass
            
            zkill_month.ships_destroyed = month.get('shipsDestroyed', 0)
            zkill_month.ships_lost = month.get('shipsLost', 0)
            zkill_month.isk_destroyed = month.get('iskDestroyed', 0)
            zkill_month.isk_lost = month.get('iskLost', 0)
            zkill_month.save()

    char_model.isk_destroyed = _stats_json.get('iskDestroyed', 0)
    char_model.isk_lost = _stats_json.get('iskLost', 0)
    char_model.all_time_sum = _stats_json.get('allTimeSum', 0)
    char_model.gang_ratio = _stats_json.get('gangRatio', 0)
    char_model.ships_destroyed = _stats_json.get('shipsDestroyed', 0)
    char_model.ships_lost = _stats_json.get('shipsLost', 0)
    char_model.solo_destroyed = _stats_json.get('soloDestroyed', 0)
    char_model.solo_lost = _stats_json.get('soloLost', 0)
    char_model.active_pvp_kills = _stats_json.get('activepvp', {}).get('kills', {}).get('count', 0)
    char_model.last_kill = _last_kill_date
    char_model.last_update = datetime.datetime.utcnow().replace(tzinfo=timezone.utc)
    char_model.save()

    #logger.info('update_character_stats for %s complete' % str(character_id))
def update_char(char_name, char_id):
    try:
        logger.info('update_character_stats for %s starting' % str(char_name))
        update_character_stats(char_id)
    except:
        logger.error('update_character_stats failed for %s' % str(char_name))
        logging.exception("Messsage")
        sleep(1)  # had an error printed it and skipped it YOLO. better wait a sec to not overload the api
        pass


@shared_task(name='authanaliticis.tasks.run_stat_model_update')
def run_stat_model_update():
    # update all corpstat'd characters
    #logger.info('start')
    active_corp_stats = CorpStats.objects.all()
    member_alliances = ['499005583', '1900696668'] # hardcoded cause *YOLO*
    stale_date = datetime.datetime.utcnow().replace(tzinfo=timezone.utc) - datetime.timedelta(hours=168)
    for cs in active_corp_stats:
        members = cs.mains
        for member in members:
            for alt in member.alts:
                if alt.alliance_id in member_alliances:
                    try:
                        if AACharacter.objects.get(character__character_id=alt.character_id).last_update<stale_date:
                            update_char(alt.character_name, alt.character_id)
                    except ObjectDoesNotExist:
                        update_char(alt.character_name, alt.character_id)

        #missing = cs.unregistered_members
        #for member in missing:
            #update_character_stats.delay(member.character_id)

def output_stats(file_output=True):
    active_corp_stats = CorpStats.objects.all()
    #member_alliances = ['499005583', '1900696668'] # hardcoded cause *YOLO*
    #for cs in active_corp_stats:
        #members = cs.mains
        #for member in members:
            #update_character_stats(member.character_id)
            #for alt in member.alts:
                #if alt.alliance_id in member_alliances:
                    #if alt.character_name != member.character_name:
                        #update_character_stats(alt.character_id)
        #missing = cs.unregistered_members
        #for member in missing:
        #    update_character_stats(member.character_id)
    out_arr=[]
    for cs in active_corp_stats:
        members = cs.mains
        for member in members:
            print("Adding: %s" % member.character.character_name)
            date_now = datetime.datetime.now()
            try:
                character = AACharacter.objects.get(character__character_id=member.character.character_id)

                qs1 = AAzKillMonth.objects.filter(year=date_now.year - 1, month__gte=date_now.month, char=character)
                qs2 = AAzKillMonth.objects.filter(year=date_now.year, char=character)
                qs = qs1 | qs2
                if date_now.month < 3:
                    qs_12m = qs.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                        'ship_destroyed_sum', 0)
                    month_6_ago = 12 + (date_now.month - 6)
                    month_3_ago = 12 + (date_now.month - 3)
                    qs_6m = qs.filter(year=date_now.year, char=character). \
                                aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                        'ship_destroyed_sum', 0) + \
                            qs.filter(year=date_now.year - 1, month__gte=month_6_ago, char=character). \
                                aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                                'ship_destroyed_sum', 0)
                    qs_3m = qs.filter(year=date_now.year, char=character). \
                                aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                        'ship_destroyed_sum', 0) + \
                            qs.filter(year=date_now.year - 1, month__gte=month_3_ago, char=character). \
                                aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                                'ship_destroyed_sum', 0)
                elif date_now.month < 6:
                    qs_12m = qs.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                        'ship_destroyed_sum', 0)
                    month_6_ago = 12 + (date_now.month - 6)
                    qs_6m = qs.filter(year=date_now.year, char=character). \
                                aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                        'ship_destroyed_sum', 0) + \
                            qs.filter(year=date_now.year - 1, month__gte=month_6_ago, char=character). \
                                aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                                'ship_destroyed_sum', 0)
                    qs_3m = qs.filter(year=date_now.year, month__gte=date_now.month - 3, char=character). \
                        aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
                else:
                    qs_12m = qs.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                        'ship_destroyed_sum', 0)
                    qs_6m = qs.filter(year=date_now.year, month__gte=date_now.month - 6, char=character). \
                        aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
                    qs_3m = qs.filter(year=date_now.year, month__gte=date_now.month - 3, char=character). \
                        aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)

                alts = [co.character for co in character.character.character_ownership.user.character_ownerships.all()]
                for alt in alts:
                    try:
                        aa_alt = AACharacter.objects.get(character=alt)
                        if not aa_alt == character:
                            qsa1 = AAzKillMonth.objects.filter(year=date_now.year - 1, month__gte=date_now.month,
                                                               char=aa_alt)
                            qsa2 = AAzKillMonth.objects.filter(year=date_now.year, char=aa_alt)
                            qsa = qsa1 | qsa2
                            if date_now.month < 3:
                                qs_12m += qsa.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                                    'ship_destroyed_sum', 0)
                                month_6_ago = 12 + (date_now.month - 6)
                                month_3_ago = 12 + (date_now.month - 3)
                                qs_6m += qsa.filter(year=date_now.year, char=character). \
                                             aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                                    'ship_destroyed_sum', 0) + \
                                         qsa.filter(year=date_now.year - 1, month__gte=month_6_ago, char=character). \
                                             aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                                             'ship_destroyed_sum', 0)
                                qs_3m += qsa.filter(year=date_now.year, char=character). \
                                             aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                                    'ship_destroyed_sum', 0) + \
                                         qsa.filter(year=date_now.year - 1, month__gte=month_3_ago, char=character). \
                                             aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                                             'ship_destroyed_sum', 0)
                            elif date_now.month < 6:
                                qs_12m += qsa.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                                    'ship_destroyed_sum', 0)
                                month_6_ago = 12 + (date_now.month - 6)
                                qs_6m += qsa.filter(year=date_now.year, char=character). \
                                             aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                                    'ship_destroyed_sum', 0) + \
                                         qsa.filter(year=date_now.year - 1, month__gte=month_6_ago, char=character). \
                                             aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                                             'ship_destroyed_sum', 0)
                                qs_3m += qsa.filter(year=date_now.year, month__gte=date_now.month - 3, char=character). \
                                    aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                                    'ship_destroyed_sum', 0)
                            else:
                                qs_12m += qsa.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                                    'ship_destroyed_sum', 0)
                                qs_6m += qsa.filter(year=date_now.year, month__gte=date_now.month - 6, char=character). \
                                    aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                                    'ship_destroyed_sum', 0)
                                qs_3m += qsa.filter(year=date_now.year, month__gte=date_now.month - 3, char=character). \
                                    aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                                    'ship_destroyed_sum', 0)
                    except:
                        pass

                out_str=[]
                out_str.append(member.character.character_name)
                out_str.append(member.character.corporation_name)
                out_str.append(str(qs_12m))
                out_str.append(str(qs_6m))
                out_str.append(str(qs_3m))
                out_arr.append(out_str)
            except:
                pass
    
    if file_output:
        with open('auth_zkill_dump.csv', 'w') as writeFile:
            writer = csv.writer(writeFile)
            writer.writerow(['Name', 'Corp', '12m', '6m', '3m'])
            writer.writerows(out_arr)
        writeFile.close()
    else:
        return out_arr
    
