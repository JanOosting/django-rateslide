# Rateslide views
# Jan Oosting 2013
#
from json import dumps, loads
import logging

from os import path
from collections import Counter
from statistics import mean, stdev

from django.shortcuts import render
from django.http import HttpResponseRedirect, Http404, HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist, SuspiciousOperation
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings

from invitation.forms import InvitationKeyForm
from histoslide.models import Slide

from .models import Case, Question, CaseInstance, Answer, AnswerAnnotation, CaseList, UserCaseList, CaseBookmark, \
                   QuestionBookmark, QuestionItem
from .forms import CaseListForm, UserCaseListSelectFormSet, tempUserFormSet, CaseInstancesSelectFormSet, \
                   CasesSelectFormSet, QuestionForm
from .utils import send_usercaselist_mail, create_anonymous_user

import numpy as np
import matplotlib
# Force matplotlib to not use any UI backend.
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, to_hex


logger = logging.getLogger(__name__)


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
    user = get_case_user(request, cl, False)
    if user:
        if check_usercaselist(user, cl) != UserCaseList.NONE:
            ud['case_completed'] = cl.cases_completed(user.pk)
            ud['case_count_completed'] = len(ud['case_completed'])
            ud['case_count_todo'] = len(cl.cases_todo(user.pk))
            ud['case_count_total'] = len(cl.cases_total(user.pk))
            ud['case_evaluation'] = cl.evaluation(user.pk)
            ud['canAdmit'] = False
        else:
            ud['canAdmit'] = cl.OpenForRegistration
        ud['isAdmin'] = is_caselist_admin(user, cl)
    else:
        ud['case_completed'] = []
        ud['case_count_completed'] = 0
        ud['case_count_todo'] = 0
        ud['case_count_total'] = 0
        ud['canAdmit'] = cl.OpenForRegistration
        ud['case_evaluation'] = ''
        ud['isAdmin'] = False
    ud['ActiveUsers'] = clu.filter(Status=UserCaseList.ACTIVE).count()
    ud['PendingUsers'] = clu.filter(Status=UserCaseList.PENDING).count()
    ud['CompleteUsers'] = clu.filter(Status=UserCaseList.COMPLETE).count()
    ud['AnonymousUsers'] = clu.filter(User__first_name='Anonymous', User__last_name='User').count()
    return {'CaseList': cl, 'Users': clu.exclude(User__first_name='Anonymous', User__last_name='User'), 'UserDict': ud}


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


@login_required()
def caselistreport(request, slug):
    try:
        cldata = get_caselist_data_by_slug(request, slug)
        if not is_caselist_admin(request.user, cldata['CaseList']):
            raise Http404
    except CaseList.DoesNotExist:
        raise Http404
    return render(request, 'rateslide/caselistreport.html', cldata)


@login_required()
def caseadd(request, slug):
    try:
        cldata = get_caselist_data_by_slug(request, slug)
        if not is_caselist_admin(request.user, cldata['CaseList']):
            raise Http404
    except CaseList.DoesNotExist:
        raise Http404
    c = Case.objects.create(Caselist = cldata['CaseList'], Name = '-- New Case --', Order = 0)
    return HttpResponseRedirect(reverse('caseadm:rateslide_case_change', args={c.pk, }))


@login_required()
def casecopy(request, case_id):
    c = Case.objects.get(pk=case_id)
    newcase = c.copy_case()
    return HttpResponseRedirect(reverse('caseadm:rateslide_case_change', args={newcase.pk, }))


@csrf_protect
@login_required()
def submitcaselist(request, caselist_id):
    cl = CaseList.objects.get(pk=caselist_id)
    if request.method == 'POST':
        clf = CaseListForm(request.POST, instance=cl)
        clf.save()
    return HttpResponseRedirect(reverse('rateslide:caselistadmin', kwargs={'slug': cl.Slug}))


def deleteemptyanonymoususercaselists(cl):
    ucl = UserCaseList.objects.filter(CaseList=cl, User__first_name='Anonymous', User__last_name='User')
    for user in ucl:
        if user.case_count_completed() == 0:
            user.delete()


@csrf_protect
@login_required()
def submitcaselistusers(request, caselist_id):
    if request.method == "POST":
        cl = CaseList.objects.get(pk=caselist_id)
        if request.POST['submit'] == 'deleteinactiveanonymous':
            deleteemptyanonymoususercaselists(cl)
        else:
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
                raise Exception('notvalid')
    else:
        raise Exception('notvalid')
    return HttpResponseRedirect(reverse('rateslide:caselistadmin', kwargs={'slug':  cl.Slug}))


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


def get_cookie_user(request, mustexist):
    if "slideobs_user" in request.COOKIES or mustexist:
        users = User.objects.filter(username=request.COOKIES["slideobs_user"])
        if users.count() == 1:
            return users[0]
        else:
            raise Http404
    else:
        # Firsttime access, create a new session user
        user = create_anonymous_user()
        request.COOKIES['slideobs_user'] = user.username
        return user


def get_case_user(request, cl, mustexist):
    if request.user.is_authenticated:
        return request.user
    else:
        if cl.VisibleForNonUsers:
            # Allow anonymous access
            user = get_cookie_user(request, mustexist)
            if check_usercaselist(user, cl) != UserCaseList.ACTIVE:
                UserCaseList.objects.create(User=user, CaseList=cl, Status=UserCaseList.ACTIVE)
            return user
        else:
            return None


@csrf_protect
def case(request, case_id):
    try:
        c = Case.objects.get(pk=case_id)
        user = get_case_user(request, c.Caselist, False)
        if not user:
            return HttpResponseRedirect(settings.LOGIN_URL)
        if check_usercaselist(user, c.Caselist) != UserCaseList.ACTIVE:
            # TODO: Return message that user is not on caselist
            raise Http404
        if not c.Caselist.is_active():
            raise Http404
        s = c.Slides.all().order_by('caseslide__order')
        editor = is_caselist_admin(user, c.Caselist)
        q_f = QuestionForm(c, user)
        # Register that user started on this case

    except Case.DoesNotExist:
        raise Http404
    response = render(request, 'rateslide/case.html', {'Case': c, 'Slides': s, 'Questions': q_f, 'Editor': editor})
    if 'slideobs_user' in request.COOKIES and user.email == '':
        response.set_cookie('slideobs_user', user.username, max_age=604800)
    return response


def showcase(request, case_id):
    try:
        c = Case.objects.get(pk=case_id)
        s = c.Slides.all().order_by('caseslide__order')
        editor = is_caselist_admin(request.user, c.Caselist)
    except Case.DoesNotExist:
        raise Http404
    return render(request, 'rateslide/showcase.html', {'Case': c, 'Slides': s, 'Editor': editor})

def caseeval(request, case_id):
    try:
        case = Case.objects.get(pk=case_id)
        user = get_case_user(request, case.Caselist, False)
        if not user:
            raise Http404
        caseinstance = CaseInstance.objects.filter(Case=case, User=user).first()
        if not caseinstance:
            raise Http404
    except Case.DoesNotExist:
        raise Http404
    s = case.Slides.all().order_by('caseslide__order')
    questions = Question.objects.filter(Case=case)
    caseinstance = CaseInstance.objects.filter(Case=case, User=user).first()
    if caseinstance:
        answers = Answer.objects.filter(CaseInstance=caseinstance).select_related('Question')
    else:
        raise Http404
    graded_answers = 0
    correct_answers = 0
    for question in questions:
        answer = answers.filter(Question = question).first()
        if answer:
            question.value = answer.textvalue()
            question.grade = answer.grade()
            if question.grade == Answer.ERROR or question.grade == Answer.CORRECT:
                graded_answers += 1
                if question.grade == Answer.CORRECT:
                    correct_answers += 1

    if graded_answers>1:
        case.answers_evaluation = '%d correct of %d' % (correct_answers, graded_answers)
    else:
        case.answers_evaluation = ''

    response = render(request, 'rateslide/caseeval.html', {'Case': case, 'Slides': s, 'Questions': questions})
    if 'slideobs_user' in request.COOKIES and user.email == '':
        response.set_cookie('slideobs_user', user.username, max_age=604800)
    return response

def next_case(request, slug):
    # Get a unprocessed case from the user
    cl = CaseList.objects.get(Slug=slug)
    user = get_case_user(request, cl, False)
    if check_usercaselist(user, cl):
        todo = cl.get_next_case(user.pk)
        if todo >= 0:
            return HttpResponseRedirect(reverse('rateslide:case', kwargs={'case_id': todo}))
        else:
            return HttpResponseRedirect(reverse('home'))
    else:
        raise Http404


def generate_report_histogram(data, question_id):
    x = np.asarray(data)

    fig, axs = plt.subplots(figsize=(3, 1))
    n, bins, patches = axs.hist(x)
    for i, patch in enumerate(patches):
        color = plt.cm.viridis(i/(len(patches)-1))
        patch.set_facecolor(color)
    fname = 'questionresult/hist_{0:d}.png'.format(question_id)
    fig.savefig(path.join(settings.MEDIA_ROOT, fname), dpi=100, bbox_inches='tight')
    return settings.MEDIA_URL + fname


def color_annotations_by(annotations, data):
    x = np.asarray(data)
    norm = Normalize(x.min(), x.max())
    for i, annot in enumerate(annotations):
        color = plt.cm.viridis(norm(x[i]))
        annot['annotation'][1]['stroke'] = to_hex(color)


@login_required()
def casereport(request, case_id):
    try:
        cs = Case.objects.get(pk=case_id)
        if not is_caselist_admin(request.user, cs.Caselist):
            raise Http404
        slides = cs.Slides.all().order_by('caseslide__order')
        questions = Question.objects.filter(Case=cs).values()
        for question in questions:
            if question['Type'] == Question.NUMERIC:
                answers = Answer.objects.filter(Question=question['id']).values_list('AnswerNumeric', flat=True)
                question['total_answers'] = answers.count()
                if answers.count() > 0:
                    question['resultimage'] = generate_report_histogram(answers, question['id'])
                    question['headings'] = ['min', 'max', 'avg', 'sd']
                    if answers.count() > 1:
                        std_dev = stdev(answers)
                    else:
                        std_dev = '-'
                    question['data'] = [(min(answers), max(answers), mean(answers), std_dev)]

            elif question['Type'] == Question.MULTIPLECHOICE:
                answers = Answer.objects.filter(Question=question['id']).values_list('AnswerNumeric', flat=True)
                question['total_answers'] = answers.count()
                if answers.count() > 0:
                    question['headings'] = ['n', '%', 'choice']
                    questionitems = QuestionItem.objects.filter(Question=question['id']).order_by('Order').\
                        values_list('Order', 'Text')
                    counter = Counter(answers)
                    question['data'] = [(counter[k], "{0:.0%}".
                                         format(counter[k]/answers.count()), n) for (k, n) in questionitems]
            elif question['Type'] == Question.DATE:
                answers = Answer.objects.filter(Question=question['id']).values_list('AnswerNumeric', flat=True)
                question['total_answers'] = answers.count()
            elif question['Type'] == Question.LINE:
                answers = Answer.objects.select_related('answerannotation').filter(Question=question['id'])
                lengths = []
                annots = []
                lengthunit = set()
                if answers.count() > 0:
                    for answ in answers:
                        if hasattr(answ, 'answerannotation'):
                            lengths.append(answ.answerannotation.Length)
                            annot = loads(answ.answerannotation.AnnotationJSON)
                            annot.append(str(answ.id))
                            annots.append({'slideid': answ.answerannotation.Slide_id, 'annotation': annot})
                            lengthunit.add(answ.answerannotation.LengthUnit)
                    question['total_answers'] = len(lengths)
                    if len(lengths) > 0:
                        question['resultimage'] = generate_report_histogram(lengths, question['id'])
                        color_annotations_by(annots, lengths)
                        if len(lengthunit) > 1:
                            lengthunit = '-'
                        else:
                            lengthunit = lengthunit.pop()
                        question['headings'] = ['min', 'max', 'avg', 'sd']
                        if len(lengths) > 1:
                            std_dev = '{0:.2g} {1:s}'.format(stdev(lengths), lengthunit)
                        else:
                            std_dev = '-'
                        question['data'] = [('{0:.2g} {1:s}'.format(min(lengths), lengthunit),
                                             '{0:.2g} {1:s}'.format(max(lengths), lengthunit),
                                             '{0:.2g} {1:s}'.format(mean(lengths), lengthunit), std_dev)]
                        question['annotations'] = dumps(annots)

            else:  # OpenText
                answers = Answer.objects.filter(Question=question['id']).exclude(AnswerText='').values_list('AnswerText', flat=True)
                question['total_answers'] = answers.count()
                if answers.count() > 0:
                    question['headings'] = ['n', '%', 'text']
                    counter = Counter(answers)
                    question['data'] = [(n, "{0:.0%}".format(n/answers.count()), t, )
                                        for (t, n) in counter.most_common(10)]

    except Case.DoesNotExist:
        raise Http404
    return render(request, 'rateslide/casereport.html', {'Case': cs, 'Slides': slides, 'Questions': questions})


@csrf_protect
def submitcase(request, case_id): 
    try:
        if request.method == 'POST':
            # Check if case has been registered by user
            cs = Case.objects.get(pk=case_id)
            user = get_case_user(request, cs.Caselist, True)
            if not (check_usercaselist(user, cs.Caselist) and user):
                raise Http404
            form = QuestionForm(cs, user, request.POST)
            if form.is_valid():
                ci, _ = CaseInstance.objects.get_or_create(Case=cs, User=user, defaults={'Status': 'E'})
                for q_id in form.cleaned_data:
                    # Check if id has proper format for question
                    # 0:'question', 1:'R|F', 2:"M|N|O|D|R|L", 3:numeric id
                    id_elts = str.split(q_id, '_')
                    if len(id_elts) == 4:
                        # Skip remarks
                        if id_elts[0] == 'question' and id_elts[2] != "R":
                            question = Question.objects.get(pk=id_elts[3])
                            ans, _ = Answer.objects.get_or_create(CaseInstance=ci, Question=question)
                            cleaned_answer = form.cleaned_data[q_id]
                            if id_elts[2] in [Question.MULTIPLECHOICE, Question.NUMERIC]:
                                if cleaned_answer != '' and cleaned_answer is not None:
                                    ans.AnswerNumeric = cleaned_answer
                                    ans.save()
                                else:
                                    ans.delete()
                            elif id_elts[2] == Question.LINE:
                                # Answer contains a JSON packed annotation
                                if cleaned_answer != '':
                                    annotation_data = loads(cleaned_answer)
                                    ans.AnswerText = "{0:.3g} {1}".format(annotation_data['length'],
                                                                          annotation_data['length_unit'])
                                    ans.save()
                                    AnswerAnnotation.objects.update_or_create(answer=ans, defaults=
                                                           {'Slide': Slide.objects.get(pk=annotation_data['slideid']),
                                                            'Length': annotation_data['length'],
                                                            'LengthUnit': annotation_data['length_unit'],
                                                            'AnnotationJSON': dumps(annotation_data['annotation'])})
                                else:
                                    if hasattr(ans, 'answerannotation'):
                                        ans.answerannotation.delete(keep_parents=True)
                                    ans.delete()
                            else:
                                if cleaned_answer != '':
                                    ans.AnswerText = cleaned_answer
                                    ans.save()
                                else:
                                    ans.delete()
                if cs.Report != "" and cs.Caselist.Type == CaseList.EXAMINATION:
                    return HttpResponseRedirect(reverse('rateslide:caseeval', kwargs={'case_id': case_id}))
                elif request.POST['submit'] == 'submit':
                    return HttpResponseRedirect(reverse('rateslide:caselist', kwargs={'slug': cs.Caselist.Slug}))
                else:
                    return next_case(request, cs.Caselist.Slug)
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
            bm_data = loads(request.body.decode('utf-8'))
            bms = CaseBookmark.objects.filter(Case=bm_data['Case'], Text=bm_data['Text'])
            if len(bms) > 0:
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
            return JsonResponse({'status': 'error', 'message': type(e).__name__ + ':' + str(e.args)}, status=400)
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
            bm_data = loads(request.body.decode('utf-8'))
            bms = QuestionBookmark.objects.filter(Question=bm_data['Question'], Text=bm_data['Text'])
            if len(bms) > 0:
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
