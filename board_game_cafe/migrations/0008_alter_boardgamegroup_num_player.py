# Generated by Django 5.1.3 on 2024-11-27 08:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('board_game_cafe', '0007_boardgamegroup_num_player'),
    ]

    operations = [
        migrations.AlterField(
            model_name='boardgamegroup',
            name='num_player',
            field=models.CharField(default='1-4 people', max_length=30),
        ),
    ]