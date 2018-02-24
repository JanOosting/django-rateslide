from __future__ import unicode_literals

from django.db import migrations

import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('rateslide', '0002_auto'),
    ]

    operations = [
        migrations.AddField(
            model_name='caselist',
            name='Slug',
            field=django_extensions.db.fields.AutoSlugField(editable=False, null=True, populate_from='Name'),
        ),
    ]
