from json import dumps, loads

from django.test import TestCase
from django.core.urlresolvers import reverse

from histoslide.models import Slide
from rateslide.models import CaseBookmark, Case, QuestionBookmark, Question


class CaseTests(TestCase):
    fixtures = ['rateslide_auth.json', 'rateslide_simplecase.json']

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_case_loads(self):
        url = reverse('rateslide:case', kwargs={'case_id': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302, 'redirect to login')
        self.client.login(username='user', password='user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rateslide/case.html')

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


class BookmarkTests(TestCase):
    fixtures = ['rateslide_auth.json', 'rateslide_simplecase.json']

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_case_bookmark_json(self):
        bm=CaseBookmark(Case=Case.objects.get(pk=1), Slide=Slide.objects.get(pk=1), CenterX=0.5, CenterY=0.5, Zoom=1.0, Text='test get', order=1)
        bm.save()
        url = reverse('rateslide:casebookmark', args=[bm.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_post_case_bookmark_empty_post(self):
        url = reverse('rateslide:casebookmark', args=[0])
        self.client.login(username='user', password='user')
        json_data = dumps({'Case': '1', 'Slide': 1, 'CenterX': 0.5 , 'CenterY': 0.5, 'Zoom':  1.0, 'Text': 'test post case', 'order': '1',})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400, 'non-json request')
        response = self.client.post(url, content_type='application/json')
        self.assertEqual(response.status_code, 400, 'empty json request')
        response = self.client.post(url, json_data, content_type='application/json')
        self.assertEqual(response.status_code, 200, 'proper json request')
        bm = CaseBookmark.objects.filter(Text__exact='test post case')
        self.assertEqual(len(bm), 1)

    def test_get_question_bookmark_json(self):
        bm=QuestionBookmark(Question=Question.objects.get(pk=1), Slide=Slide.objects.get(pk=1), CenterX=0.5, CenterY=0.5, Zoom=1.0, Text='test get', order=1)
        bm.save()
        url = reverse('rateslide:questionbookmark', args=[bm.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_post_question_bookmark_empty_post(self):
        url = reverse('rateslide:questionbookmark', args=[0])
        self.client.login(username='user', password='user')
        json_data = dumps({'Question': '1', 'Slide': 1, 'CenterX': 0.5 , 'CenterY': 0.5, 'Zoom':  1.0, 'Text': 'test post question', 'order': '1',})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400, 'non-json request')
        response = self.client.post(url, content_type='application/json')
        self.assertEqual(response.status_code, 400, 'empty json request')
        response = self.client.post(url, json_data, content_type='application/json')
        self.assertEqual(response.status_code, 200, 'proper json request')
        bm = QuestionBookmark.objects.filter(Text__exact='test post question')
        self.assertEqual(len(bm), 1)
        self.assertAlmostEqual(bm[0].CenterX, 0.5)

    def test_post_question_bookmark_same_text_updates_bookmark(self):
        url = reverse('rateslide:questionbookmark', args=[0])
        self.client.login(username='user', password='user')
        json_data = dumps({'Question': '1', 'Slide': 1, 'CenterX': 0.5 , 'CenterY': 0.5, 'Zoom':  1.0, 'Text': 'test question twice', 'order': '1',})
        response = self.client.post(url, json_data, content_type='application/json')
        json_data = dumps({'Question': '1', 'Slide': 1, 'CenterX': 0.8 , 'CenterY': 0.8, 'Zoom':  2.0, 'Text': 'test question twice', 'order': '2',})
        response = self.client.post(url, json_data, content_type='application/json')
        bm = QuestionBookmark.objects.filter(Text__exact='test question twice')
        self.assertEqual(len(bm), 1)
        self.assertAlmostEqual(bm[0].CenterX, 0.8)

    def test_post_case_bookmark_same_text_updates_bookmark(self):
        url = reverse('rateslide:casebookmark', args=[0])
        self.client.login(username='user', password='user')
        json_data = dumps({'Case': '1', 'Slide': 1, 'CenterX': 0.5 , 'CenterY': 0.3, 'Zoom':  1.0, 'Text': 'test case twice', 'order': '1',})
        response = self.client.post(url, json_data, content_type='application/json')
        json_data = dumps({'Case': '1', 'Slide': 1, 'CenterX': 0.8 , 'CenterY': 0.9, 'Zoom':  2.0, 'Text': 'test case twice', 'order': '2',})
        response = self.client.post(url, json_data, content_type='application/json')
        bm = CaseBookmark.objects.filter(Text__exact='test case twice')
        self.assertEqual(len(bm), 1)
        self.assertAlmostEqual(bm[0].CenterY, 0.9)

    def test_delete_question_bookmark(self):
        bm=QuestionBookmark(Question=Question.objects.get(pk=1), Slide=Slide.objects.get(pk=1), CenterX=0.5, CenterY=0.5, Zoom=1.0, Text='test delete', order=1)
        bm.save()
        url = reverse('rateslide:questionbookmark', args=[bm.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404, 'user should be logged in')
        self.client.login(username='user', password='user')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404, 'only admins can delete, status: %d in stead of 404' % response.status_code)
        self.client.login(username='admin', password='admin')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200, 'proper deletion')
        bms=QuestionBookmark.objects.filter(Text='test delete', Question=1)
        self.assertEqual(len(bms), 0, 'Book mark should be deleted')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404, 'object should be deleted by previous call')


