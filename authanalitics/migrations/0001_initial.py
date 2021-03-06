# Generated by Django 2.0.5 on 2019-01-06 12:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('eveonline', '0010_alliance_ticker'),
    ]

    operations = [
        migrations.CreateModel(
            name='AACharacter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('isk_destroyed', models.IntegerField(default=0)),
                ('isk_lost', models.IntegerField(default=0)),
                ('all_time_sum', models.IntegerField(default=0)),
                ('gang_ratio', models.IntegerField(default=0)),
                ('ships_destroyed', models.IntegerField(default=0)),
                ('ships_lost', models.IntegerField(default=0)),
                ('solo_destroyed', models.IntegerField(default=0)),
                ('solo_lost', models.IntegerField(default=0)),
                ('active_pvp_kills', models.IntegerField(default=0)),
                ('last_kill', models.DateTimeField(default=None, null=True)),
                ('character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='eveonline.EveCharacter')),
            ],
        ),
        migrations.CreateModel(
            name='AAzKillMonth',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(default=0)),
                ('month', models.IntegerField(default=0)),
                ('ships_destroyed', models.IntegerField(default=0)),
                ('ships_lost', models.IntegerField(default=0)),
                ('isk_destroyed', models.IntegerField(default=0)),
                ('isk_lost', models.IntegerField(default=0)),
                ('char', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authanalitics.AACharacter')),
            ],
        ),
    ]
