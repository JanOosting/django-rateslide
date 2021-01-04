from json import dumps, loads

from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from histoslide.models import Slide
from rateslide.models import CaseBookmark, Case, CaseInstance, QuestionBookmark, Question, CaseList, Answer, \
                             UserCaseList
from rateslide.views import deleteemptyanonymoususercaselists, get_caselist_data
from rateslide.utils import create_anonymous_user
from .utils import populate_answers


class CaseTests(TestCase):
    fixtures = ['rateslide_auth.json', 'rateslide_simplecase.json']

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_case_loads(self):
        usercount = User.objects.count()
        cl = CaseList.objects.get(pk=1)
        cl.VisibleForNonUsers = False
        cl.save()
        url = reverse('rateslide:case', kwargs={'case_id': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302, 'redirect to login')
        self.client.login(username='user', password='user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rateslide/case.html')
        self.assertEqual(User.objects.count(), usercount, 'Usercount should stay the same')

    def test_case_post(self):
        cl = CaseList.objects.get(pk=1)
        cl.VisibleForNonUsers = False
        cl.save()
        url = reverse('rateslide:submitcase', kwargs={'case_id': 1})
        response = self.client.post(url, {'question_R_M_1': '1', 'question_F_R_2': 'Test', 'submit': 'submit', })
        self.assertEqual(response.status_code, 404, 'Error')
        self.client.login(username='user', password='user')
        response = self.client.post(url, {'question_R_M_1': '1', 'question_F_R_2': 'Test', 'submit': 'submit', })
        self.assertEqual(response.status_code, 302)
        ci = CaseInstance.objects.filter(Case__id=1, User=User.objects.get(username='user'))
        self.assertEqual(ci.count(), 1, 'case was only answered once')
        ans = Answer.objects.filter(CaseInstance=ci[0].pk)
        self.assertEqual(ans.count(), 1, 'should be 1 answer in case, remark is skipped')
        self.assertEqual(ans[0].AnswerNumeric, 1)

    def test_case_post_optional_MC_empty(self):
        cl = CaseList.objects.get(pk=1)
        cl.VisibleForNonUsers = False
        cl.save()
        url = reverse('rateslide:submitcase', kwargs={'case_id': 4})
        response = self.client.post(url, {'submit': 'submit', })
        self.assertEqual(response.status_code, 404, 'Error')
        self.client.login(username='user', password='user')
        response = self.client.post(url, {'submit': 'submit', })
        self.assertEqual(response.status_code, 302)
        ci = CaseInstance.objects.filter(Case__id=4, User=User.objects.get(username='user'))
        self.assertEqual(ci.count(), 1, 'case was only answered once')
        ans = Answer.objects.filter(CaseInstance=ci[0].pk)
        self.assertEqual(ans.count(), 0, 'should be 0 answer in case, Optional answer not given')

    def test_case_post_optional_numeric_empty(self):
        cl = CaseList.objects.get(pk=1)
        cl.VisibleForNonUsers = False
        cl.save()
        url = reverse('rateslide:submitcase', kwargs={'case_id': 5})
        self.client.login(username='user', password='user')
        response = self.client.post(url, {'submit': 'submit', })
        self.assertEqual(response.status_code, 302)
        ci = CaseInstance.objects.filter(Case__id=5, User=User.objects.get(username='user'))
        self.assertEqual(ci.count(), 1, 'case was only answered once')
        ans = Answer.objects.filter(CaseInstance=ci[0].pk)
        self.assertEqual(ans.count(), 0, 'should be 0 answer in case, Optional answer not given')

    def test_case_update(self):
        cl = CaseList.objects.get(pk=1)
        cl.VisibleForNonUsers = False
        cl.save()
        url = reverse('rateslide:submitcase', kwargs={'case_id': 1})
        self.client.login(username='user', password='user')
        self.client.post(url, {'question_R_M_1': '1', 'question_F_R_2': 'Test', 'submit': 'submit', })
        self.client.post(url, {'question_R_M_1': '3', 'question_F_R_2': 'Test', 'submit': 'submit', })
        ci = CaseInstance.objects.filter(Case__id=1, User=User.objects.get(username='user'))
        self.assertEqual(len(ci), 1, 'There should be only 1 case instance after update')
        ans = Answer.objects.filter(CaseInstance=ci[0])
        self.assertEqual(len(ans), 1, 'should be 1 answer in caseinstance')
        self.assertEqual(ans[0].AnswerNumeric, 3)

    def test_case_visiblefornonusers_allows_anonymous(self):
        usercount = User.objects.count()
        cl = CaseList.objects.get(pk=1)
        cl.VisibleForNonUsers = True
        cl.save()
        url = reverse('rateslide:case', kwargs={'case_id': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rateslide/case.html')
        self.assertEqual(User.objects.count(), usercount+1, 'A anonymous user should be created')
        url = reverse('rateslide:case', kwargs={'case_id': 3})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), usercount+1, 'In a second case the same user should be used')
        user = User.objects.get(first_name='Anonymous')
        self.assertEqual(len(user.username), 30, 'username:%s length is not 30' % user.username)

    def test_caselist_loads(self):
        url = reverse('rateslide:caselist', kwargs={'slug': 'simple-case'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rateslide/caselist.html')

    def test_showcase_loads(self):
        url = reverse('rateslide:showcase', kwargs={'case_id': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rateslide/showcase.html')

    def test_showcaselist_loads(self):
        url = reverse('rateslide:showcaselist', kwargs={'slug': 'simple-showcase'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rateslide/showcaselist.html')

    def test_caselistadmin_loads(self):
        url = reverse('rateslide:caselistadmin', kwargs={'slug': 'simple-case'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302, 'redirect to login')
        self.client.login(username='user', password='user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404,
                         'Caselistadmin is exclusive for admins, status: %s in stead of 404' % response.status_code)
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rateslide/caselistadmin.html')

    def test_caselistreport_loads(self):
        url = reverse('rateslide:caselistreport', kwargs={'slug': 'simple-case'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302, 'redirect to login')
        self.client.login(username='user', password='user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404,
                         'Caselistreport is exclusive for admins, status: %s in stead of 404' % response.status_code)
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rateslide/caselistreport.html')

    def test_casereport_loads(self):
        url = reverse('rateslide:casereport', kwargs={'case_id': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302, 'redirect to login')
        self.client.login(username='user', password='user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404,
                         'CaseReport is exclusive for admins, status: %s in stead of 404' % response.status_code)
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rateslide/casereport.html')
        self.assertContains(response, 'questionreport', count=2)

    def test_usercaselist_loads(self):
        url = reverse('rateslide:usercaselist', kwargs={'usercaselist_id': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302, 'redirect to login')
        self.client.login(username='user', password='user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404,
                         'Usercaselist is exclusive for admins, status: %s in stead of 404' % response.status_code)
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rateslide/usercaselist.html')

    def test_populate_case_answers(self):
        case = populate_answers(1)
        url = reverse('rateslide:casereport', kwargs={'case_id': case.id})
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        self.assertContains(response, 'questionreport', count=4)

    def test_line_answer_without_annotation(self):
        cl = CaseList.objects.get(pk=1)
        case = Case.objects.create(Name='Exam case generated 2', Caselist=cl, Introduction='Test')
        q4 = Question.objects.create(Case=case, Type=Question.LINE, Text='measure line', Order=1)
        user = User.objects.create(username='UserTest')
        ci = CaseInstance.objects.create(Case=case, User=user, Status=CaseInstance.ENDED)
        Answer.objects.create(CaseInstance=ci, Question=q4, AnswerText='')
        url = reverse('rateslide:casereport', kwargs={'case_id': case.id})
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        self.assertContains(response, 'questionreport', count=1)

    def test_caseeval_loads(self):
        caseinstance = CaseInstance.objects.get(pk=2)
        self.client.login(username='user', password='user')
        url = reverse('rateslide:caseeval', kwargs={'caseinstance_id': caseinstance.id})
        self.client.get(url)



class BookmarkTests(TestCase):
    fixtures = ['rateslide_auth.json', 'rateslide_simplecase.json']

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_case_bookmark_json(self):
        bm = CaseBookmark(Case=Case.objects.get(pk=1), Slide=Slide.objects.get(pk=1), CenterX=0.5, CenterY=0.5,
                          Zoom=1.0, Text='test get', order=1)
        bm.save()
        url = reverse('rateslide:casebookmark', args=[bm.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_post_case_bookmark_empty_post(self):
        url = reverse('rateslide:casebookmark', args=[0])
        self.client.login(username='user', password='user')
        json_data = dumps({'Case': '1', 'Slide': 1, 'CenterX': 0.5, 'CenterY': 0.5,
                           'Zoom':  1.0, 'Text': 'test post case', 'order': '1', })
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400, 'non-json request')

        response = self.client.post(url, content_type='application/json')
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.status_code, 400, 'empty json request')
        self.assertEqual(loads(response.content)['status'], 'error')
        self.assertIn('KeyError', loads(response.content)['message'])

        response = self.client.post(url, json_data, content_type='application/json')
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.status_code, 200, 'proper json request')
        self.assertEqual(loads(response.content)['status'], 'OK')
        self.assertEqual(loads(response.content)['message'], '')

        bm = CaseBookmark.objects.filter(Text__exact='test post case')
        self.assertEqual(len(bm), 1)

    def test_get_question_bookmark_json(self):
        bm = QuestionBookmark(Question=Question.objects.get(pk=1), Slide=Slide.objects.get(pk=1), CenterX=0.5,
                              CenterY=0.5, Zoom=1.0, Text='test get', order=1)
        bm.save()
        url = reverse('rateslide:questionbookmark', args=[bm.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_post_question_bookmark_empty_post(self):
        url = reverse('rateslide:questionbookmark', args=[0])
        self.client.login(username='user', password='user')
        json_data = dumps({'Question': '1', 'Slide': 1, 'CenterX': 0.5, 'CenterY': 0.5, 'Zoom':  1.0,
                           'Text': 'test post question', 'order': '1', })
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400, 'non-json request')

        response = self.client.post(url, content_type='application/json')
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.status_code, 400, 'empty json request')
        self.assertEqual(loads(response.content)['status'], 'error')
        self.assertIn('KeyError', loads(response.content)['message'])

        response = self.client.post(url, json_data, content_type='application/json')
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.status_code, 200, 'proper json request')
        self.assertEqual(loads(response.content)['status'], 'OK')
        self.assertEqual(loads(response.content)['message'], '')

        bm = QuestionBookmark.objects.filter(Text__exact='test post question')
        self.assertEqual(len(bm), 1)
        self.assertAlmostEqual(bm[0].CenterX, 0.5)

    def test_post_question_bookmark_same_text_updates_bookmark(self):
        url = reverse('rateslide:questionbookmark', args=[0])
        self.client.login(username='user', password='user')
        json_data = dumps({'Question': '1', 'Slide': 1, 'CenterX': 0.5, 'CenterY': 0.5, 'Zoom':  1.0,
                           'Text': 'test question twice', 'order': '1', })
        self.client.post(url, json_data, content_type='application/json')
        json_data = dumps({'Question': '1', 'Slide': 1, 'CenterX': 0.8, 'CenterY': 0.8, 'Zoom':  2.0,
                           'Text': 'test question twice', 'order': '2', })
        self.client.post(url, json_data, content_type='application/json')
        bm = QuestionBookmark.objects.filter(Text__exact='test question twice')
        self.assertEqual(len(bm), 1)
        self.assertAlmostEqual(bm[0].CenterX, 0.8)

    def test_post_case_bookmark_same_text_updates_bookmark(self):
        url = reverse('rateslide:casebookmark', args=[0])
        self.client.login(username='user', password='user')
        json_data = dumps({'Case': '1', 'Slide': 1, 'CenterX': 0.5, 'CenterY': 0.3, 'Zoom':  1.0,
                           'Text': 'test case twice', 'order': '1', })
        self.client.post(url, json_data, content_type='application/json')
        json_data = dumps({'Case': '1', 'Slide': 1, 'CenterX': 0.8, 'CenterY': 0.9, 'Zoom':  2.0,
                           'Text': 'test case twice', 'order': '2', })
        self.client.post(url, json_data, content_type='application/json')
        bm = CaseBookmark.objects.filter(Text__exact='test case twice')
        self.assertEqual(len(bm), 1)
        self.assertAlmostEqual(bm[0].CenterY, 0.9)

    def test_delete_question_bookmark(self):
        bm = QuestionBookmark(Question=Question.objects.get(pk=1), Slide=Slide.objects.get(pk=1), CenterX=0.5,
                              CenterY=0.5, Zoom=1.0, Text='test delete', order=1)
        bm.save()
        url = reverse('rateslide:questionbookmark', args=[bm.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404, 'user should be logged in')
        self.client.login(username='user', password='user')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404,
                         'only admins can delete, status: %d in stead of 404' % response.status_code)
        self.client.login(username='admin', password='admin')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200, 'proper deletion')
        bms = QuestionBookmark.objects.filter(Text='test delete', Question=1)
        self.assertEqual(len(bms), 0, 'Book mark should be deleted')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404, 'object should be deleted by previous call')

    def test_delete_case_bookmark(self):
        bm = CaseBookmark(Case=Case.objects.get(pk=1), Slide=Slide.objects.get(pk=1), CenterX=0.5,
                          CenterY=0.5, Zoom=1.0, Text='test delete 1', order=1)
        bm.save()
        url = reverse('rateslide:casebookmark', args=[bm.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404, 'user should be logged in')
        self.client.login(username='user', password='user')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404,
                         'only admins can delete, status: %d in stead of 404' % response.status_code)
        self.client.login(username='admin', password='admin')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200, 'proper deletion')
        bms = CaseBookmark.objects.filter(Text='test delete 1', Case=1)
        self.assertEqual(len(bms), 0, 'Book mark should be deleted')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404, 'object should be deleted by previous call')


def createcaselist(cltype):
    cl = CaseList.objects.create(Name='admintest',
                                 Owner=User.objects.get(username='caselistowner'),
                                 Abstract='abstract',
                                 Description='description',
                                 InviteMail='-',
                                 WelcomeMail='-',
                                 ReminderMail='-',
                                 Type=cltype)
    Case.objects.create(Name='admintest-case', Caselist=cl, Introduction='intro')
    return cl


class CaseListAdminTests(TestCase):
    fixtures = ['rateslide_auth.json', 'rateslide_simplecase.json']

    def prepare_anonymous_users_in_caselist(self):
        caselist = createcaselist(CaseList.EXAMINATION)
        caselist.VisibleForNonUsers = True  # Make sure anonymous is accepted
        caselist.save()
        self.client.login(username='caselistowner', password='caselistowner')
        return caselist

    def test_DeleteEmptyAnonymousUserCaseLists_no_users(self):
        caselist = self.prepare_anonymous_users_in_caselist()
        usercount = caselist.user_count()
        deleteemptyanonymoususercaselists(caselist)
        self.assertEqual(caselist.user_count(), usercount, 'nothing happened')

    def test_DeleteEmptyAnonymousUserCaseLists_single__empty_anonymous(self):
        caselist = self.prepare_anonymous_users_in_caselist()
        user = create_anonymous_user()
        UserCaseList.objects.create(User=user, CaseList=caselist, Status=UserCaseList.ACTIVE)
        usercount = caselist.user_count()
        deleteemptyanonymoususercaselists(caselist)
        ucl = UserCaseList.objects.filter(CaseList=caselist, User=user)
        self.assertEqual(caselist.user_count(), usercount-1, 'inactive anonymous user deleted')
        self.assertEqual(ucl.count(), 0, 'the just creasted user is not in UserCaseList anymore')

    def test_DeleteEmptyAnonymousUserCaseLists_multiple__empty_anonymous(self):
        caselist = self.prepare_anonymous_users_in_caselist()
        user = create_anonymous_user()
        UserCaseList.objects.create(User=user, CaseList=caselist, Status=UserCaseList.ACTIVE)
        UserCaseList.objects.create(User=create_anonymous_user(), CaseList=caselist, Status=UserCaseList.ACTIVE)
        usercount = caselist.user_count()
        deleteemptyanonymoususercaselists(caselist)
        ucl = UserCaseList.objects.filter(CaseList=caselist, User=user)
        self.assertEqual(caselist.user_count(), usercount-2, 'inactive anonymous user deleted')
        self.assertEqual(ucl.count(), 0, 'the just creasted user is not in UserCaseList anymore')

    def test_DeleteEmptyAnonymousUserCaseLists_single_active_anonymous(self):
        caselist = self.prepare_anonymous_users_in_caselist()
        user = create_anonymous_user()
        UserCaseList.objects.create(User=user, CaseList=caselist, Status=UserCaseList.ACTIVE)
        CaseInstance.objects.create(Case=Case.objects.get(Name='admintest-case'), User=user, Status=CaseInstance.ENDED)
        usercount = caselist.user_count()
        deleteemptyanonymoususercaselists(caselist)
        ucl = UserCaseList.objects.filter(CaseList=caselist, User=user)
        self.assertEqual(caselist.user_count(), usercount, 'active anonymous user is not deleted')
        self.assertEqual(ucl.count(), 1, 'the just creasted user is still in UserCaseList')

    def test_Do_not_show_anonymous(self):
        caselist = self.prepare_anonymous_users_in_caselist()
        anoninactiveuser = create_anonymous_user()
        UserCaseList.objects.create(User=anoninactiveuser, CaseList=caselist, Status=UserCaseList.ACTIVE)
        anonactiveuser = create_anonymous_user()
        UserCaseList.objects.create(User=anonactiveuser, CaseList=caselist, Status=UserCaseList.ACTIVE)
        CaseInstance.objects.create(Case=Case.objects.get(Name='admintest-case'), User=anonactiveuser,
                                    Status=CaseInstance.ENDED)
        inactiveuser = User.objects.create_user(username='MyActive', first_name='Active', last_name='User')
        UserCaseList.objects.create(User=inactiveuser, CaseList=caselist, Status=UserCaseList.ACTIVE)

        ucl = UserCaseList.objects.filter(CaseList=caselist)
        self.assertEqual(ucl.count(), 4, 'All users added')

        request = HttpRequest()
        request.user = User.objects.get(username='caselistowner')
        ucldata = get_caselist_data(request, caselist)
        self.assertEqual(ucldata['Users'].count(), 2, 'Only contains MyActive and caselistowner')
