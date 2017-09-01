from django import forms
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.template import Template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.encoding import force_text


# Copied from
# http://djangosnippets.org/snippets/2785/
# 16-6-2013
# Change radiobutton to put input outside of and before label 
class ButtonRadioSelect(forms.RadioSelect):
    """Radio Select with overridden renderer, placing labels after inputs.

    To make 3d stateful buttons, add CSS::

        <style type="text/css">
          ul.form-button-radio li {display: inline-block;}
          ul.form-button-radio input[type="radio"] {display: none}
          ul.form-button-radio input[type="radio"]+label {
            padding: 2px;
            border-radius: 5px;
            -moz-border-radius: 5px;
            -webkit-border-radius: 5px;
            border: 2px outset #BBB;
            cursor: pointer;
          }
          ul.form-button-radio input[type="radio"]:checked+label {
            font-weight: bold;
            background-color: #999;
            color: white;
          }
        </style>

    """

    class ButtonRadioInput(forms.widgets.RadioChoiceInput):

        def __unicode__(self):
            # No idea, why Superclass' __unicode__ does not call
            # correct render() method
            return self.render()

        def render(self, name=None, value=None, attrs=None, choices=()):
            if 'id' in self.attrs:
                label_for = ' for="%s"' % (self.attrs['id'])
            else:
                label_for = ''
            choice_label = conditional_escape(force_text(self.choice_label))
            return mark_safe(u'%s <label%s>%s</label>' % (self.tag(), label_for, choice_label))

    class ButtonRadioFieldRenderer(forms.widgets.RadioFieldRenderer):
        def __iter__(self):
            for i, choice in enumerate(self.choices):
                yield ButtonRadioSelect.ButtonRadioInput(self.name, self.value, self.attrs.copy(), choice, i)

        def __getitem__(self, idx):
            choice = self.choices[idx]  # Let the IndexError propogate
            return ButtonRadioSelect.ButtonRadioInput(self.name, self.value, self.attrs.copy(), choice, idx)

        def render(self):
            """Outputs a <ul> for this set of radio fields."""
            return mark_safe(u'<ul class="form-button-radio">\n%s\n</ul>'
                             % u'\n'.join([u'<li>%s</li>' % force_text(w) for w in self]))

    renderer = ButtonRadioFieldRenderer
    

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
