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

logger = logging.getLogger(__name__)

@shared_task
def update_character_stats(character_id):
    logger.debug('update_character_stats for %s starting' % str(character_id))
    # https://zkillboard.com/api/stats/characterID/####/
    _stats_request = requests.get("https://zkillboard.com/api/stats/characterID/" + str(character_id) + "/")
    _stats_json = _stats_request.json()
    
    # https://zkillboard.com/api/characterID/####/kills/
    _kills_request = requests.get("https://zkillboard.com/api/characterID/" + str(character_id) + "/kills/")
    _kills_json = _kills_request.json()
    
    _last_kill_date = None
    if len(_kills_json) > 0:
        # https://esi.evetech.net/latest/killmails/ID####/HASH####/?datasource=tranquility
        _last_kill_request = requests.get("https://esi.evetech.net/latest/killmails/" + str(_kills_json[0]['killmail_id']) + "/" + str(_kills_json[0]['zkb']['hash']) + "/?datasource=tranquility")
        _last_kill_json = _last_kill_request.json()
        try:
            _last_kill_date = parse_datetime(_last_kill_json['killmail_time'])
        except:
            pass

    char_model, created = AACharacter.objects.update_or_create(character = EveCharacter.objects.get(character_id=int(character_id)))
    if created:
        pass
    
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
    char_model.save() 
    
    if len(_stats_json.get('months', [])) > 0:
        for key, month in _stats_json.get('months', []).items():
            zkill_month, created = AAzKillMonth.objects.update_or_create(char=char_model, year=month.get('year', 0), month=month.get('month', 0))
            if created:
                pass
            
            zkill_month.ships_destroyed = month.get('shipsDestroyed', 0)
            zkill_month.ships_lost = month.get('shipsLost', 0)
            zkill_month.isk_destroyed = month.get('iskDestroyed', 0)
            zkill_month.isk_lost = month.get('iskLost', 0)
            zkill_month.save()

    logger.debug('update_character_stats for %s complete' % str(character_id))

@shared_task(name='authanaliticis.tasks.run_stat_model_update')
def run_stat_model_update():
    # update all corpstat'd characters
    active_corp_stats = CorpStats.objects.all()
    member_alliances = ['499005583', '1900696668'] # hardcoded cause *YOLO*
    for cs in active_corp_stats:
        members = cs.mains
        for member in members:
            update_character_stats.delay(member.character_id)
            for alt in member.alts:
                if alt.alliance_id in member_alliances:
                    if alt.character_name != member.character_name:
                        update_character_stats.delay(alt.character_id)
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

                qs1 = AAzKillMonth.objects.filter(year=date_now.year-1, month__gte=date_now.month, char=character)
                qs2 = AAzKillMonth.objects.filter(year=date_now.year, char=character)
                qs = qs1 | qs2
                qs_12m = qs.order_by('-year', '-month').aggregate(ship_destroyed_sum=Sum('ships_destroyed'))['ship_destroyed_sum']
                qs_6m = qs.order_by('-year', '-month')[:6].aggregate(ship_destroyed_sum=Sum('ships_destroyed'))['ship_destroyed_sum']
                qs_3m = qs.order_by('-year', '-month')[:3].aggregate(ship_destroyed_sum=Sum('ships_destroyed'))['ship_destroyed_sum']

                alts = [co.character for co in character.character.character_ownership.user.character_ownerships.all()]
                for alt in alts:
                    try:
                        aa_alt = AACharacter.objects.get(character=alt)
                        if not aa_alt == character:
                            qsa1 = AAzKillMonth.objects.filter(year=date_now.year - 1, month__gte=date_now.month, char=aa_alt)
                            qsa2 = AAzKillMonth.objects.filter(year=date_now.year, char=aa_alt)
                            qsa = qsa1 | qsa2
                            qs_12m += qsa.order_by('-year', '-month').aggregate(ship_destroyed_sum=Sum('ships_destroyed'))[
                                'ship_destroyed_sum']
                            qs_6m += qsa.order_by('-year', '-month')[:6].aggregate(ship_destroyed_sum=Sum('ships_destroyed'))[
                                'ship_destroyed_sum']
                            qs_3m += qsa.order_by('-year', '-month')[:3].aggregate(ship_destroyed_sum=Sum('ships_destroyed'))[
                                'ship_destroyed_sum']
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
    
