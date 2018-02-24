from django.db import migrations

import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('rateslide', '0004_caselist_slug_populate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='caselist',
            name='Slug',
            field=django_extensions.db.fields.AutoSlugField(editable=False, unique=True, populate_from='Name'),
        ),
    ]
