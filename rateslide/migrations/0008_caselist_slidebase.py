# Generated by Django 3.0.7 on 2020-06-07 16:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rateslide', '0007_answerannotation'),
    ]

    operations = [
        migrations.AddField(
            model_name='caselist',
            name='SlideBase',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
