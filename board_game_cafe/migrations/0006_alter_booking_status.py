# Generated by Django 5.1.3 on 2024-11-27 08:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('board_game_cafe', '0005_alter_rental_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='status',
            field=models.CharField(default='booked', max_length=30),
        ),
    ]
