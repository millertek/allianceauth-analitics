from django import template
from django.db.models import Sum

import datetime

from authanalitics.models import AACharacter, AAzKillMonth

register = template.Library()


@register.filter(name='get_ytd_kills_single')
def get_ytd_kills_single(input_id):
    try:
        date_now = datetime.datetime.now()
        character = AACharacter.objects.get(character__character_id=input_id)
        qs1 = AAzKillMonth.objects.filter(year=date_now.year-1, month__gte=date_now.month, char=character)
        qs2 = AAzKillMonth.objects.filter(year=date_now.year, char=character)
        qs = qs1 | qs2
        qs_12m = qs.order_by('-year', '-month').aggregate(ship_destroyed_sum=Sum('ships_destroyed'))['ship_destroyed_sum']
        qs_6m = qs.order_by('-year', '-month')[:6].aggregate(ship_destroyed_sum=Sum('ships_destroyed'))['ship_destroyed_sum']
        qs_3m = qs.order_by('-year', '-month')[:3].aggregate(ship_destroyed_sum=Sum('ships_destroyed'))['ship_destroyed_sum']

        return "<td class=\"text-center\">%s</td><td class=\"text-center\">%s</td><td class=\"text-center\">%s</td>" % (str(qs_12m), str(qs_6m), str(qs_3m))

    except:
        return "<td class=\"text-center\">%s</td><td class=\"text-center\">%s</td><td class=\"text-center\">%s</td>" % (str(0), str(0), str(0))


@register.filter(name='get_ytd_kills_account')
def get_ytd_kills_account(input_id):
    try:
        date_now = datetime.datetime.now()
        character = AACharacter.objects.get(character__character_id=input_id)

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
            return "<td class=\"text-center\" style=\"vertical-align:middle\">%s</td><td class=\"text-center\" style=\"vertical-align:middle\">%s</td><td class=\"text-center\" style=\"vertical-align:middle\">%s</td>" % (str(qs_12m), str(qs_6m), str(qs_3m))

    except:
        return "<td class=\"text-center\" style=\"vertical-align:middle\">%s</td><td class=\"text-center\" style=\"vertical-align:middle\">%s</td><td class=\"text-center\" style=\"vertical-align:middle\">%s</td>" % (str(0), str(0), str(0))
