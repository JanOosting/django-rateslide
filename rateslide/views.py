# Rateslide views
# Jan Oosting 2013
# 
from json import dumps, loads

from django.shortcuts import render
from django.http import HttpResponseRedirect, Http404, HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist, SuspiciousOperation
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib.auth.decorators import login_required

from invitation.forms import InvitationKeyForm
from histoslide.models import Slide

from .models import Case, Question, CaseInstance, Answer, CaseList, UserCaseList, CaseBookmark, QuestionBookmark
from .forms import CaseListForm, UserCaseListSelectFormSet, tempUserFormSet, CaseInstancesSelectFormSet, \
                   CasesSelectFormSet, QuestionForm
from .utils import send_usercaselist_mail

                
def check_usercaselist(user, cl):
    ucl = UserCaseList.objects.filter(User=user, CaseList=cl)
    if ucl.exists():
        return ucl[0].Status 
    else:
        return UserCaseList.NONE


def is_caselist_admin(user, cl):
    return cl.Owner == user or user.is_staff


def get_caselist_data_by_id(request, caselist_id):
    cl = CaseList.objects.get(pk=caselist_id)
    return get_caselist_data(request, cl)


def get_caselist_data_by_slug(request, slug):
    cl = CaseList.objects.get(Slug=slug)
    return get_caselist_data(request, cl)


def get_caselist_data(request, cl):
    clu = UserCaseList.objects.filter(CaseList=cl)
    ud = {}
    if request.user.is_authenticated:
        if check_usercaselist(request.user, cl) != UserCaseList.NONE:
            ud['case_count_completed'] = len(cl.cases_completed(request.user.pk))
            ud['case_count_todo'] = len(cl.cases_todo(request.user.pk))
            ud['case_count_total'] = len(cl.cases_total(request.user.pk))
            ud['canAdmit'] = False
        else:
            ud['canAdmit'] = cl.OpenForRegistration
        ud['isAdmin'] = is_caselist_admin(request.user, cl)
    else:
        ud['case_count_completed'] = 0
        ud['case_count_todo'] = 0
        ud['case_count_total'] = 0
        ud['canAdmit'] = cl.OpenForRegistration
        ud['isAdmin'] = False
    ud['ActiveUsers'] = clu.filter(Status=UserCaseList.ACTIVE).count()
    ud['PendingUsers'] = clu.filter(Status=UserCaseList.PENDING).count()
    ud['CompleteUsers'] = clu.filter(Status=UserCaseList.COMPLETE).count()
    return {'CaseList': cl, 'Users': clu, 'UserDict': ud}


def caselist(request, slug):
    try:
        cldata = get_caselist_data_by_slug(request, slug)
    except CaseList.DoesNotExist:
        raise Http404
    return render(request, 'rateslide/caselist.html', cldata)


def showcaselist(request, slug):
    try:
        cldata = get_caselist_data_by_slug(request, slug)
    except CaseList.DoesNotExist:
        raise Http404
    return render(request, 'rateslide/showcaselist.html', cldata)


@csrf_protect
@login_required()
def caselistadmin(request, slug):
    try:
        cldata = get_caselist_data_by_slug(request, slug)
        if not is_caselist_admin(request.user, cldata['CaseList']):
            raise Http404
        cldata['CaseListForm'] = CaseListForm(instance=cldata['CaseList'])
        cldata['UserFormSet'] = UserCaseListSelectFormSet(queryset=cldata['Users'], initial=[{'selected': u'on', }])
        cldata['InviteUser'] = InvitationKeyForm()
    except CaseList.DoesNotExist:
        raise Http404
    return render(request, 'rateslide/caselistadmin.html', cldata)
  

@csrf_protect
@login_required()
def submitcaselist(request, caselist_id):    
    if request.method == 'POST':
        cl = CaseList.objects.get(pk=caselist_id)
        clf = CaseListForm(request.POST, instance=cl)
        clf.save()
    return HttpResponseRedirect(reverse('rateslide:caselistadmin', kwargs={'slug': cl.Slug}))


@csrf_protect
@login_required()
def submitcaselistusers(request, caselist_id):
    if request.method == "POST":
        ucl = tempUserFormSet(request.POST, request.FILES)
        if ucl.is_valid():
            if request.POST['submit'] == 'submitactivate':
                for userform in ucl:
                    if userform.cleaned_data['selected']:
                        user = UserCaseList.objects.get(pk=userform.cleaned_data['id'])
                        if user.Status == UserCaseList.PENDING:
                            # Set all selected users to active, send mail
                            user.Status = UserCaseList.ACTIVE
                            user.save()
                            send_usercaselist_mail(user, 'welcome')
            if request.POST['submit'] == 'submitreminder':
                for userform in ucl:
                    if userform.cleaned_data['selected']:
                        user = UserCaseList.objects.get(pk=userform.cleaned_data['id'])
                        if user.Status == UserCaseList.ACTIVE:
                            send_usercaselist_mail(user, 'reminder')
        else:
            raise Exception("notvalid")
    return HttpResponseRedirect(reverse('rateslide:caselistadmin', kwargs={'caselist_id': caselist_id}))


@csrf_protect
@login_required()
def usercaselist(request, usercaselist_id):
    try:
        ucl = UserCaseList.objects.get(pk=usercaselist_id)
        cldata = get_caselist_data_by_id(request, ucl.CaseList.pk)
        if not is_caselist_admin(request.user, cldata['CaseList']):
            raise Http404
        cases = Case.objects.filter(Caselist=ucl.CaseList)
        usercases = CaseInstance.objects.filter(User=ucl.User, Case__in=cases)
        cases = cases.exclude(id__in=usercases.values_list('Case', flat=True))
        cldata['Cases'] = CasesSelectFormSet(queryset=cases, initial=[{'selected': u'on', }])
        cldata['CaseInstances'] = CaseInstancesSelectFormSet(queryset=usercases, initial=[{'selected': u'on', }])
        cldata['UserCaseList'] = ucl
        return render(request, 'rateslide/usercaselist.html', cldata)
    except ObjectDoesNotExist:
        raise Http404


@csrf_protect
@login_required()
def submitusercaselist(request, usercaselist_id):
    if request.method == "POST":
        tmplst = tempUserFormSet(request.POST, request.FILES)
        ucl = UserCaseList.objects.get(pk=usercaselist_id)
        if tmplst.is_valid():
            if request.POST['submit'] == 'submitcases':
                for userform in tmplst:
                    if userform.cleaned_data['selected']:
                        caseinstance = CaseInstance(Case=Case.objects.get(pk=userform.cleaned_data['id']),
                                                    User=ucl.User, Status='S')
                        caseinstance.save()
            if request.POST['submit'] == 'submitcaseinstances':
                for userform in tmplst:
                    if userform.cleaned_data['selected']:
                        caseinstance = CaseInstance.objects.get(pk=userform.cleaned_data['id'])
                        caseinstance.delete()
        else:
            raise Exception("notvalid")
    return HttpResponseRedirect(reverse('rateslide:usercaselist', kwargs={'usercaselist_id': usercaselist_id}))


@csrf_protect
@login_required()
def case(request, case_id):
    try:
        c = Case.objects.get(pk=case_id)
        if check_usercaselist(request.user, c.Caselist) != UserCaseList.ACTIVE:
            # TODO: Return message that user is not on caselist
            raise Http404
        s = c.Slides.all().order_by('caseslide__order')
        editor = is_caselist_admin(request.user, c.Caselist)
        q_f = QuestionForm(Question.objects.filter(Case=c.id))
        # Register that user started on this case
    except Case.DoesNotExist:
        raise Http404
    return render(request, 'rateslide/case.html', {'Case': c, 'Slides': s, 'Questions': q_f, 'Editor': editor})


def showcase(request, case_id):
    try:
        c = Case.objects.get(pk=case_id)
        s = c.Slides.all().order_by('caseslide__order')
        editor = is_caselist_admin(request.user, c.Caselist)
    except Case.DoesNotExist:
        raise Http404
    return render(request, 'rateslide/showcase.html', {'Case': c, 'Slides': s, 'Editor': editor})


@login_required()
def next_case(request, slug):
    # Get a unprocessed case from the user
    cl = CaseList.objects.get(Slug=slug)
    if check_usercaselist(request.user, cl):
        todo = cl.get_next_case(request.user.pk)
        if todo >= 0:
            return HttpResponseRedirect(reverse('rateslide:case', kwargs={'case_id': todo}))
        else:
            return HttpResponseRedirect(reverse('home'))
    else:
        raise Http404
           

@csrf_protect
def submitcase(request, case_id): 
    try:
        if request.method == 'POST':
            # Check if case has been registered by user
            cs = Case.objects.get(pk=case_id)
            if not check_usercaselist(request.user, cs.Caselist):
                raise Http404
            form = QuestionForm(Question.objects.filter(Case=cs.id), request.POST)
            if form.is_valid():
                ci = CaseInstance(Case=cs, User=request.user, Status='E')
                ci.save()
                for q_id in request.POST:
                    # Check if id has proper format for question
                    # 0:'question', 1:'R|F', 2:"M|N|O|D|R", 3:numeric
                    id_elts = str.split(q_id, '_')
                    if len(id_elts) == 4:
                        if id_elts[0] == 'question' and id_elts[2] != "R":
                            question = Question.objects.get(pk=id_elts[3])
                            ans = Answer(CaseInstance=ci, Question=question)
                            if id_elts[2] in [Question.MULTIPLECHOICE, Question.NUMERIC]:
                                ans.AnswerNumeric = request.POST[q_id]
                            else:
                                ans.AnswerText = request.POST[q_id]
                            ans.save()
                if request.POST['submit'] == 'submit':
                    return HttpResponseRedirect('/')
                else:
                    return next_case(request, cs.Caselist.id)
            else:
                return render(request, 'rateslide/case.html',
                              {'Case': cs, 'Slides': cs.Slides.all(), 'Questions': form})
    except Case.DoesNotExist:
        raise Http404


@login_required()
def apply_for_invitation(request, slug):
    # Request to enter a case list
    cl = CaseList.objects.get(Slug=slug)
    if check_usercaselist(request.user, cl) == UserCaseList.NONE:
        if cl.SelfRegistration:
            ucl = UserCaseList(User=request.user, CaseList=cl, Status=UserCaseList.ACTIVE)
            # TODO: Send welcome mail
        else:
            ucl = UserCaseList(User=request.user, CaseList=cl, Status=UserCaseList.PENDING)
        # TODO: send mail to owner of caselist
        ucl.save()
        return HttpResponseRedirect('/')    
    else:
        # User is already registered for this list
        return HttpResponseRedirect('/')

@csrf_exempt
def casebookmark(request, bookmark_id):
    # Get a JSON object with bookmark data
    if request.method == 'POST':
        if request.content_type != 'application/json':
            raise SuspiciousOperation
        try:
            bm_data = loads(request.body)
            bms = CaseBookmark.objects.filter(Case=bm_data['Case'], Text=bm_data['Text'])
            if len(bms)>0:
                bm = bms[0]
            else:
                bm = CaseBookmark()
            bm.Slide = Slide.objects.get(pk=bm_data['Slide'])
            bm.Case = Case.objects.get(pk=bm_data['Case'])
            bm.CenterX = bm_data['CenterX']
            bm.CenterY = bm_data['CenterY']
            bm.Zoom = bm_data['Zoom']
            bm.Text = bm_data['Text']
            bm.full_clean()
            bm.save()
            return JsonResponse({'status': 'OK', 'message': ''}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': type(e).__name__ +':'+str(e.args)}, status=400)
    if request.method == 'DELETE':
        try:
            bm = CaseBookmark.objects.get(pk=bookmark_id)
        except ObjectDoesNotExist:
            raise Http404
        if not is_caselist_admin(request.user, bm.Case.Caselist):
            raise Http404
        bm.delete()
        return HttpResponse(dumps("OK"), content_type="application/json")
    else:
        bm = CaseBookmark.objects.get(pk=bookmark_id)
        response_data = {'Case': bm.Case.pk, 'Slide': bm.Slide.pk, 'CenterX': bm.CenterX, 'CenterY': bm.CenterY,
                         'Zoom': bm.Zoom, 'Text': bm.Text}
        return HttpResponse(dumps(response_data), content_type="application/json")

@csrf_exempt
def questionbookmark(request, bookmark_id):
    # Get a JSON object with bookmark data
    if request.method == 'POST':
        if request.content_type != 'application/json':
            raise SuspiciousOperation
        try:
            bm_data = loads(request.body)
            bms = QuestionBookmark.objects.filter(Question=bm_data['Question'], Text=bm_data['Text'])
            if len(bms)>0:
                bm = bms[0]
            else:
                bm = QuestionBookmark()
            bm.Slide = Slide.objects.get(pk=bm_data['Slide'])
            bm.Question = Question.objects.get(pk=bm_data['Question'])
            bm.CenterX = bm_data['CenterX']
            bm.CenterY = bm_data['CenterY']
            bm.Zoom = bm_data['Zoom']
            bm.Text = bm_data['Text']
            bm.full_clean()
            bm.save()
            return JsonResponse({'status': 'OK', 'message': ''}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': type(e).__name__ + ':' + str(e.args)}, status=400)
    if request.method == 'DELETE':
        try:
            bm = QuestionBookmark.objects.get(pk=bookmark_id)
        except ObjectDoesNotExist:
            raise Http404
        if not is_caselist_admin(request.user, bm.Question.Case.Caselist):
            raise Http404
        bm.delete()
        return HttpResponse(dumps("OK"), content_type="application/json")
    else:
        bm = QuestionBookmark.objects.get(pk=bookmark_id)
        response_data = {'Question': bm.Question.pk, 'Slide': bm.Slide.pk, 'CenterX': bm.CenterX, 'CenterY': bm.CenterY,
                         'Zoom': bm.Zoom, 'Text': bm.Text}
        return HttpResponse(dumps(response_data), content_type="application/json")
