import string
import random

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.urls import reverse
from django.template import Template
from django.template.defaulttags import register


def get_usercaselist_mailbody(usercaselist, mail_type):
    """
    Send an email to a member of a usercaselist
    Make string substitutions for several variables
    %first_name%
    %last_name%
    %username%
    %deadline%
    %caselisturl%
    """
    def substitute_variables(body):
        body = body.replace('%first_name%', usercaselist.User.first_name)
        body = body.replace('%last_name%', usercaselist.User.last_name)
        body = body.replace('%username%', usercaselist.User.username)
        body = body.replace('%deadline%', usercaselist.CaseList.EndDate.strftime('%d-%m-%Y'))
        body = body.replace('%caselisturl%', str(Site.objects.get_current()) + reverse('rateslide:caselist',
                            args=[usercaselist.CaseList.id, ]))
        return body
    if mail_type == 'invite':
        message = substitute_variables(usercaselist.CaseList.InviteMail)
    elif mail_type == 'welcome':
        message = substitute_variables(usercaselist.CaseList.WelcomeMail)
    elif mail_type == 'reminder':
        message = substitute_variables(usercaselist.CaseList.ReminderMail)
    else:
        message = "Invalid mail_type"
    return message


def get_mailbody(context, templatestr):
    t = Template(templatestr)
    return t.render(context)


def send_usercaselist_mail(usercaselist, mail_type):
    send_mail(mail_type, get_usercaselist_mailbody(usercaselist, mail_type), usercaselist.CaseList.Owner.email,
              [usercaselist.User.email])


def random_string(length):
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))


ANONONYMOUS_NAME_LENGTH = 30


def create_anonymous_user():
    return User.objects.create_user(username=random_string(ANONONYMOUS_NAME_LENGTH),
                                    first_name='Anonymous', last_name='User')

@register.filter
def get_choice(choices, value):
    for li in choices:
        if li[0]==value:
            return li[1]
