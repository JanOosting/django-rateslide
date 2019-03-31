from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.admin.sites import AdminSite

from rateslide.admin import NewUserAdmin
from rateslide.utils import create_anonymous_user
from rateslide.models import UserCaseList, CaseInstance, CaseList, Case, Answer, Question


class UserAdminTests(TestCase):
    fixtures = ['rateslide_auth.json', 'rateslide_simplecase.json']

    def test_DoNotDeleteNonAnonymous(self):
        users = User.objects.all()
        usercount = users.count()
        ua = NewUserAdmin(User, AdminSite)
        ua.delete_inactive_anonymous_users(1, 1)

        users = User.objects.all()
        self.assertEqual(usercount, users.count(), 'No users should be deleted')

    def test_DeleteAnonymousUserWithoutUserCaseList(self):
        anon1 = create_anonymous_user()
        users = User.objects.all()
        usercount = users.count()

        ua = NewUserAdmin(User, AdminSite)
        ua.delete_inactive_anonymous_users(1, 1)

        users = User.objects.all()
        self.assertEqual(usercount - 1, users.count(), 'One user should be deleted')
        users = User.objects.filter(username=anon1.username)
        self.assertEqual(0, users.count(), 'Created user should not be in user list')

    def test_DoNotDeleteAnonymousWithAnsweredCases(self):
        anon1 = create_anonymous_user()
        users = User.objects.all()
        usercount = users.count()
        cl = CaseList.objects.get(pk=1)
        # add user to caselist
        UserCaseList.objects.create(User=anon1, CaseList=cl, Status=UserCaseList.ACTIVE)
        # Answer a question
        case = Case.objects.get(pk=1)
        ci = CaseInstance.objects.create(Case=case, User=anon1, Status=CaseInstance.ENDED)
        question = Question.objects.get(pk=1)
        Answer.objects.create(CaseInstance=ci, Question=question, AnswerNumeric=2)

        ua = NewUserAdmin(User, AdminSite)
        ua.delete_inactive_anonymous_users(1, 1)

        users = User.objects.all()
        self.assertEqual(usercount, users.count(), 'This user should not be deleted')
        users = User.objects.filter(username=anon1.username)
        self.assertEqual(1, users.count(), 'Created user should still be in user list')

    def test_DeleteAnonymousUserWithEmptyCaseList(self):
        anon1 = create_anonymous_user()
        users = User.objects.all()
        usercount = users.count()
        cl = CaseList.objects.get(pk=1)
        # add user to caselist
        UserCaseList.objects.create(User=anon1, CaseList=cl, Status=UserCaseList.ACTIVE)

        ua = NewUserAdmin(User, AdminSite)
        ua.delete_inactive_anonymous_users(1, 1)

        users = User.objects.all()
        self.assertEqual(usercount - 1, users.count(), 'One user should be deleted')
        users = User.objects.filter(username=anon1.username)
        self.assertEqual(0, users.count(), 'Created user should not be in user list')
