from django.db import migrations

from rateslide.models import CaseList

def migrate_data_forward(apps, schema_editor):
    for instance in CaseList.objects.all():
        print("Generating slug for %s" % instance)
        instance.save() # Will trigger slug update

def migrate_data_backward(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('rateslide', '0003_caselist_slug'),
    ]

    operations = [
        migrations.RunPython(
            migrate_data_forward,
            migrate_data_backward,
        ),
    ]
