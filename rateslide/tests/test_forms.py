from datetime import date

from django.test import TestCase
from django.forms.widgets import TextInput, NumberInput, RadioSelect, DateInput, HiddenInput, Textarea
from django.contrib.auth.models import User
from rateslide.forms import QuestionForm

from rateslide.models import Question, CaseInstance, Answer, AnswerAnnotation

from .utils import create_case_with_all_question_types


class QuestionFormTests(TestCase):
    fixtures = ['rateslide_auth.json', 'rateslide_simplecase.json']

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_form_contains_fields(self):
        case = create_case_with_all_question_types()
        form = QuestionForm(case, None)
        questions = Question.objects.filter(Case=case)
        self.assertEqual(len(questions), len(form.fields))

    def test_questionfields_widgets(self):
        case = create_case_with_all_question_types()
        form = QuestionForm(case, None)
        question = Question.objects.get(Case=case, Type=Question.OPENTEXT)
        field = form.fields[question.fieldid()]
        self.assertTrue(isinstance(field.widget, Textarea))
        question = Question.objects.get(Case=case, Type=Question.NUMERIC)
        field = form.fields[question.fieldid()]
        self.assertTrue(isinstance(field.widget, NumberInput))
        question = Question.objects.get(Case=case, Type=Question.MULTIPLECHOICE)
        field = form.fields[question.fieldid()]
        self.assertTrue(isinstance(field.widget, RadioSelect))
        question = Question.objects.get(Case=case, Type=Question.DATE)
        field = form.fields[question.fieldid()]
        self.assertTrue(isinstance(field.widget, DateInput))
        question = Question.objects.get(Case=case, Type=Question.REMARK)
        field = form.fields[question.fieldid()]
        self.assertTrue(isinstance(field.widget, HiddenInput))
        question = Question.objects.get(Case=case, Type=Question.LINE)
        field = form.fields[question.fieldid()]
        self.assertTrue(isinstance(field.widget, HiddenInput))

    def test_questionfield_answertype(self):
        case = create_case_with_all_question_types()
        user = User.objects.get(username='user')
        data = {}
        question_opentext = Question.objects.get(Case=case, Type=Question.OPENTEXT)
        data[question_opentext.fieldid()] = 'plain text'
        question_numeric = Question.objects.get(Case=case, Type=Question.NUMERIC)
        data[question_numeric.fieldid()] = '5'
        question_multiplechoice = Question.objects.get(Case=case, Type=Question.MULTIPLECHOICE)
        data[question_multiplechoice.fieldid()] = '1'
        question_date = Question.objects.get(Case=case, Type=Question.DATE)
        data[question_date.fieldid()] = '2018-1-10'
        question_remark = Question.objects.get(Case=case, Type=Question.REMARK)
        data[question_remark.fieldid()] = 'test'
        question_line = Question.objects.get(Case=case, Type=Question.LINE)
        data[question_line.fieldid()] = '{"length": 2, "length_unit": "mm", "slideid": 1, "annotation": ["line", {"x1": "1.0", "y1": "1.0", "x2": "25.0", "y2": "25.0", "stroke": "green", "stroke-width": "3", "vector-effect": "non-scaling-stroke"}]'
        form = QuestionForm(case, user, data)
        self.assertTrue(form.is_valid(), 'Form should validate ok')
        self.assertEqual(form.cleaned_data[question_opentext.fieldid()], 'plain text')
        self.assertEqual(form.cleaned_data[question_numeric.fieldid()], 5)
        self.assertEqual(form.cleaned_data[question_multiplechoice.fieldid()], 1)
        self.assertEqual(form.cleaned_data[question_date.fieldid()], date(2018, 1, 10))
        self.assertEqual(form.cleaned_data[question_remark.fieldid()], 'test')
        self.assertEqual(form.cleaned_data[question_line.fieldid()], '{"length": 2, "length_unit": "mm", "slideid": 1, "annotation": ["line", {"x1": "1.0", "y1": "1.0", "x2": "25.0", "y2": "25.0", "stroke": "green", "stroke-width": "3", "vector-effect": "non-scaling-stroke"}]')

    def test_questionfield_from_previously_saved_answer(self):
        case = create_case_with_all_question_types()
        user = User.objects.get(username='user')
        caseinstance = CaseInstance.objects.create(Case=case, User=user)
        question_opentext = Question.objects.get(Case=case, Type=Question.OPENTEXT)
        Answer.objects.create(CaseInstance=caseinstance, Question=question_opentext, AnswerText='answer opentext')
        question_numeric = Question.objects.get(Case=case, Type=Question.NUMERIC)
        Answer.objects.create(CaseInstance=caseinstance, Question=question_numeric, AnswerNumeric=20)
        question_multiplechoice = Question.objects.get(Case=case, Type=Question.MULTIPLECHOICE)
        Answer.objects.create(CaseInstance=caseinstance, Question=question_multiplechoice, AnswerNumeric=2)
        question_date = Question.objects.get(Case=case, Type=Question.DATE)
        Answer.objects.create(CaseInstance=caseinstance, Question=question_date, AnswerText='2018-02-13')
        question_remark = Question.objects.get(Case=case, Type=Question.REMARK)
        question_line = Question.objects.get(Case=case, Type=Question.LINE)
        lineanswer = Answer.objects.create(CaseInstance=caseinstance, Question=question_line, AnswerText='1.5 mm')
        AnswerAnnotation.objects.create(answer=lineanswer, Slide_id=1, Length=1.5, LengthUnit='mm', AnnotationJSON='["line", {"x1": "1.0", "y1": "1.0", "x2": "30.0", "y2": "30.0", "stroke": "green", "stroke-width": "3", "vector-effect": "non-scaling-stroke"}]')
        form = QuestionForm(case, user)
        self.assertTrue(form.is_valid(), 'Form should validate ok')
        self.assertEqual(form.cleaned_data[question_opentext.fieldid()], 'answer opentext')
        self.assertEqual(form.cleaned_data[question_numeric.fieldid()], 20)
        self.assertEqual(form.cleaned_data[question_multiplechoice.fieldid()], 2)
        self.assertEqual(form.cleaned_data[question_date.fieldid()], date(2018, 2, 13))
        self.assertEqual(form.cleaned_data[question_remark.fieldid()], '')
        self.assertEqual(form.cleaned_data[question_line.fieldid()], '{"length": 1.5, "length_unit": "mm", "slideid": 1, "annotation": ["line", {"x1": "1.0", "y1": "1.0", "x2": "30.0", "y2": "30.0", "stroke": "green", "stroke-width": "3", "vector-effect": "non-scaling-stroke"}]}')
