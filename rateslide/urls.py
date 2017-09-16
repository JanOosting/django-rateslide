from django.conf.urls import url

from . import views

app_name = 'rateslide'

urlpatterns = [
    url(r'^apply/(?P<slug>.+)/$', views.apply_for_invitation, name='apply-for-invitation'),
    url(r'^caselist/(?P<slug>.+)/$', views.caselist, name='caselist'),
    url(r'^showcaselist/(?P<slug>.+)/$', views.showcaselist, name='showcaselist'),
    url(r'^caselistadmin/(?P<slug>.+)/$', views.caselistadmin, name='caselistadmin'),
    url(r'^submitcaselist/(?P<caselist_id>\d+)/$', views.submitcaselist, name='submitcaselist'),
    url(r'^submitcaselistusers/(?P<caselist_id>\d+)/$', views.submitcaselistusers, name='submitcaselistusers'),
    url(r'^usercaselist/(?P<usercaselist_id>\d+)/$', views.usercaselist, name='usercaselist'),
    url(r'^submitusercaselist/(?P<usercaselist_id>\d+)/$', views.submitusercaselist, name='submitusercaselist'),
    url(r'^case/(?P<case_id>\d+)/$', views.case, name='case'),
    url(r'^showcase/(?P<case_id>\d+)/$', views.showcase, name='showcase'),
    url(r'^nextcase/(?P<slug>.+)/$', views.next_case, name='next-case'),
    url(r'^submitcase/(?P<case_id>\d+)/$', views.submitcase, name='submitcase'),
    url(r'^getbookmark/(?P<bookmark_id>\d+)/$', views.get_bookmark, name='get_bookmark'),
    url(r'^submitbookmark/$', views.submitbookmark, name='submitbookmark'),
]
