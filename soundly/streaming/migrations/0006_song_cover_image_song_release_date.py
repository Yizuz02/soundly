# Generated by Django 5.1.2 on 2025-01-09 08:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('streaming', '0005_songhistory_likedsong'),
    ]

    operations = [
        migrations.AddField(
            model_name='song',
            name='cover_image',
            field=models.ImageField(blank=True, null=True, upload_to='album_covers/'),
        ),
        migrations.AddField(
            model_name='song',
            name='release_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
