# Generated by Django 5.1.3 on 2024-11-26 17:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('board_game_cafe', '0002_booking_status_rental_return_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='password',
            field=models.CharField(default=None, max_length=30),
        ),
    ]
