from django import template
from django.db.models import Sum
from django.db.models.functions import Coalesce
from dateutil.relativedelta import relativedelta

import datetime

from authanalitics.models import AACharacter, AAzKillMonth

register = template.Library()


@register.filter(name='get_ytd_kills_single')
def get_ytd_kills_single(input_id, month=None):
    try:
        if not month:  # Just testing shit
            date_now = datetime.datetime.now()
        else:
            date_now = datetime.datetime.now() - relativedelta(months=month)
            print(date_now)

        character = AACharacter.objects.get(character__character_id=input_id)
        qs1 = AAzKillMonth.objects.filter(year=date_now.year-1, month__gte=date_now.month, char=character)
        qs2 = AAzKillMonth.objects.filter(year=date_now.year, month__lte=date_now.month, char=character)
        qs = qs1 | qs2
        if date_now.month<3:
            qs_12m = qs.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
            month_6_ago = 12+(date_now.month-6)
            month_3_ago = 12+(date_now.month-3)
            qs_6m = qs.filter(year=date_now.year, char=character). \
                    aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0) + \
                    qs.filter(year=date_now.year - 1, month__gte=month_6_ago, char=character). \
                        aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
            qs_3m = qs.filter(year=date_now.year, char=character). \
                    aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0) + \
                    qs.filter(year=date_now.year - 1, month__gte=month_3_ago, char=character). \
                        aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
        elif date_now.month<6:
            qs_12m = qs.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
            month_6_ago = 12+(date_now.month-6)
            qs_6m = qs.filter(year=date_now.year, char=character). \
                    aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0) + \
                    qs.filter(year=date_now.year - 1, month__gte=month_6_ago, char=character). \
                        aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
            qs_3m = qs.filter(year=date_now.year, month__gte=date_now.month-3, char=character). \
                        aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
        else:
            qs_12m = qs.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
            qs_6m = qs.filter(year=date_now.year, month__gte=date_now.month-6, char=character). \
                        aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
            qs_3m = qs.filter(year=date_now.year, month__gte=date_now.month-3, char=character). \
                    aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)



        return "<td class=\"text-center\">%s</td><td class=\"text-center\">%s</td><td class=\"text-center\">%s</td>" % \
               (str(qs_12m if qs_12m else 0), str(qs_6m if qs_6m else 0), str(qs_3m if qs_3m else 0))

    except:
        return "<td class=\"text-center\">%s</td><td class=\"text-center\">%s</td><td class=\"text-center\">%s</td>" % (str(0), str(0), str(0))


@register.filter(name='get_ytd_kills_account')
def get_ytd_kills_account(input_id, month=None):
    try:
        if not month:  # Just testing shit
            date_now = datetime.datetime.now()
        else:
            date_now = datetime.datetime.now() - relativedelta(months=month)
            print(date_now)

        character = AACharacter.objects.get(character__character_id=input_id)

        qs1 = AAzKillMonth.objects.filter(year=date_now.year-1, month__gte=date_now.month, char=character)
        qs2 = AAzKillMonth.objects.filter(year=date_now.year, char=character)
        qs = qs1 | qs2
        if date_now.month < 3:
            qs_12m = qs.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
            month_6_ago = 12 + (date_now.month - 6)
            month_3_ago = 12 + (date_now.month - 3)
            qs_6m = qs.filter(year=date_now.year, char=character). \
                        aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0) + \
                    qs.filter(year=date_now.year - 1, month__gte=month_6_ago, char=character). \
                        aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
            qs_3m = qs.filter(year=date_now.year, char=character). \
                        aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0) + \
                    qs.filter(year=date_now.year - 1, month__gte=month_3_ago, char=character). \
                        aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
        elif date_now.month < 6:
            qs_12m = qs.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
            month_6_ago = 12 + (date_now.month - 6)
            qs_6m = qs.filter(year=date_now.year, char=character). \
                        aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0) + \
                    qs.filter(year=date_now.year - 1, month__gte=month_6_ago, char=character). \
                        aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
            qs_3m = qs.filter(year=date_now.year, month__gte=date_now.month - 3, char=character). \
                aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
        else:
            qs_12m = qs.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
            qs_6m = qs.filter(year=date_now.year, month__gte=date_now.month - 6, char=character). \
                aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
            qs_3m = qs.filter(year=date_now.year, month__gte=date_now.month - 3, char=character). \
                aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)

        alts = [co.character for co in character.character.character_ownership.user.character_ownerships.all()]
        for alt in alts:
            try:
                aa_alt = AACharacter.objects.get(character=alt)
                if not aa_alt == character:
                    qsa1 = AAzKillMonth.objects.filter(year=date_now.year - 1, month__gte=date_now.month, char=aa_alt)
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
                            aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum',
                                                                                                  0)
                    else:
                        qs_12m += qsa.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                            'ship_destroyed_sum', 0)
                        qs_6m += qsa.filter(year=date_now.year, month__gte=date_now.month - 6, char=character). \
                            aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum',
                                                                                                  0)
                        qs_3m += qsa.filter(year=date_now.year, month__gte=date_now.month - 3, char=character). \
                            aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum',
                                                                                                  0)
            except:
                pass
        return "<td class=\"text-center\" style=\"vertical-align:middle\">%s</td><td class=\"text-center\" style=\"vertical-align:middle\">%s</td><td class=\"text-center\" style=\"vertical-align:middle\">%s</td>" % \
               (str(qs_12m if qs_12m else 0), str(qs_6m if qs_6m else 0), str(qs_3m if qs_3m else 0))

    except:
        return "<td class=\"text-center\" style=\"vertical-align:middle\">%s</td><td class=\"text-center\" style=\"vertical-align:middle\">%s</td><td class=\"text-center\" style=\"vertical-align:middle\">%s</td>" % (str(0), str(0), str(0))
