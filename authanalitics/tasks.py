import logging
import requests

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

def output_stats():
    active_corp_stats = CorpStats.objects.all()
    member_alliances = ['499005583', '1900696668'] # hardcoded cause *YOLO*
    for cs in active_corp_stats:
        members = cs.mains
        for member in members:
            update_character_stats(member.character_id)
            for alt in member.alts:
                if alt.alliance_id in member_alliances:
                    if alt.character_name != member.character_name:
                        update_character_stats(alt.character_id)
        #missing = cs.unregistered_members
        #for member in missing:
        #    update_character_stats(member.character_id)
    out_str=""
    for cs in active_corp_stats:
        members = cs.mains
        for member in members:
            c_stat = AACharacter.objects.get(character=member.character)
            total_kills = c_stat.ships_destroyed
            total_losses = c_stat.ships_lost
            total_year_losses = AAzKillMonth.objects.filter(char=c_stat, year=2018).aggregate(ship_lost_sum=Sum('ships_lost'))['ship_lost_sum']
            total_year_kills = AAzKillMonth.objects.filter(char=c_stat, year=2018).aggregate(ship_destroyed_sum=Sum('ships_destroyed'))['ship_destroyed_sum']
         #   print(total_kills)
          #  print(total_losses)
           # print(total_year_losses)
            #print(total_year_kills)
            alt_str = ""
            for alt in member.alts:
                if alt.alliance_id in member_alliances:
                    if alt.character_name != member.character_name:
                       a_stat = AACharacter.objects.get(character=alt)
                       total_kills += a_stat.ships_destroyed
                       total_losses += a_stat.ships_lost
                       total_year_losses +=  AAzKillMonth.objects.filter(char=a_stat, year=2018).aggregate(ship_lost_sum=Sum('ships_lost'))['ship_lost_sum']
                       total_year_kills +=  AAzKillMonth.objects.filter(char=a_stat, year=2018).aggregate(ship_destroyed_sum=Sum('ships_destroyed'))['ship_destroyed_sum']
                       alt_str += ","
                       alt_str += alt.character_name
            out_str+=member.character.character_name
            out_str+=","            
            out_str+=member.character.corporation_name
            out_str+=","
            out_str+=str(total_kills)
            out_str+=","
            out_str+=str(total_losses)
            out_str+=","
            out_str+=str(total_year_kills)
            out_str+=","
            out_str+=str(total_year_losses)
            out_str+=alt_str
            out_str+="\n"
    print(out_str)
    with open('MassOutput.csv', 'w') as f:
        f.write(out_str)
