=================
 django-rateslide
=================

Questionnaires and presentations with histoslide

Installation
------------

1. Add "rateslide" and 'django.forms' to your INSTALLED_APPS setting like this. Make sure that 'rateslide' comes before 'django.forms'.:

    INSTALLED_APPS = [
        ...
        'histoslide',
        'rateslide',
        'django.forms',

    ]

2. Set TEMPLATES['BACKEND'] to 'django.template.backends.django.DjangoTemplates'
