from django.contrib import admin

# Register your models here.
from .models import AACharacter, AAzKillMonth

admin.site.register(AACharacter)

class month(admin.ModelAdmin):
    list_display=('char', 'year', 'month')
    search_fields = ['char__character__character_name']
    ordering = ('char','-year','month')
admin.site.register(AAzKillMonth, month)

