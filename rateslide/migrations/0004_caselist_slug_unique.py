from django.db import migrations

import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('rateslide', '0003_caselist_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='caselist',
            name='Slug',
            field=django_extensions.db.fields.AutoSlugField(editable=False, unique=True, blank=True, populate_from='Name', overwrite=False),
        ),
    ]
