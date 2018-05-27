from django.test import TestCase

from rateslide.models import Question


class QuestionTests(TestCase):
    fixtures = ['rateslide_auth.json', 'rateslide_simplecase.json']

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_field_id(self):
        question = Question.objects.get(pk=1)
        self.assertEqual(question.fieldid(), 'question_R_M_1')

        question = Question.objects.create(Case_id=1, Type=Question.NUMERIC, Required=False, Order=3, Text='Question 3')
        self.assertEqual(question.fieldid(), 'question_F_N_' + str(question.id))
