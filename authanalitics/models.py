from django.db import models
from allianceauth.eveonline.models import EveCharacter

# Character Stats
class AACharacter(models.Model):
    character = models.ForeignKey(EveCharacter, on_delete=models.CASCADE)
    isk_destroyed = models.BigIntegerField(default=0)
    isk_lost = models.BigIntegerField(default=0)
    all_time_sum = models.IntegerField(default=0)
    gang_ratio = models.IntegerField(default=0)
    ships_destroyed = models.IntegerField(default=0)
    ships_lost = models.IntegerField(default=0)
    solo_destroyed = models.IntegerField(default=0)
    solo_lost = models.IntegerField(default=0)
    active_pvp_kills = models.IntegerField(default=0)
    last_kill = models.DateTimeField(null=True, default=None)
    
    def __str__(self):
        return self.character.character_name


# Monthly Character Stats
class AAzKillMonth(models.Model):
    char = models.ForeignKey(AACharacter, on_delete=models.CASCADE)
    year = models.IntegerField(default=0)
    month = models.IntegerField(default=0)
    ships_destroyed = models.IntegerField(default=0)
    ships_lost = models.IntegerField(default=0)
    isk_destroyed = models.BigIntegerField(default=0)
    isk_lost = models.BigIntegerField(default=0)

    def __str__(self):
        return "%s for %s/%s" %(self.char.character.character_name, str(self.month), str(self.year))