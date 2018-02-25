from __future__ import unicode_literals

from django.db import migrations

import django_extensions.db.fields

from rateslide.models import CaseList

def migrate_data_forward(apps, schema_editor):
    for instance in CaseList.objects.all():
        print("Generating slug for %s" % instance)
        instance.save() # Will trigger slug update

def migrate_data_backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('rateslide', '0002_auto'),
    ]

    operations = [
        migrations.AddField(
            model_name='caselist',
            name='Slug',
            field=django_extensions.db.fields.AutoSlugField(editable=False, null=True, blank=True, populate_from='Name', overwrite=True),
        ),
        migrations.RunPython(
            migrate_data_forward,
            migrate_data_backward,
        ),
    ]
