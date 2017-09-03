from django.test import TestCase
from django.core.urlresolvers import reverse


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
        url = reverse('rateslide:caselist', kwargs={'caselist_id': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rateslide/caselist.html')

    def test_showcase_loads(self):
        url = reverse('rateslide:showcase', kwargs={'case_id': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rateslide/showcase.html')

    def test_showcaselist_loads(self):
        url = reverse('rateslide:showcaselist', kwargs={'caselist_id': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rateslide/showcaselist.html')

    def test_caselistadmin_loads(self):
        url = reverse('rateslide:caselistadmin', kwargs={'caselist_id': 1})
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
