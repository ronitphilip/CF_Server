# Generated by Django 5.1.2 on 2025-03-21 17:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('colleges', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='college',
            old_name='city',
            new_name='district',
        ),
    ]
