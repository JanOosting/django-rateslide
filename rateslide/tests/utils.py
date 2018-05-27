
from django.contrib.auth.models import User
from rateslide.models import Case, CaseInstance, Answer, Question, QuestionItem, UserCaseList, AnswerAnnotation


def populate_answers(count):
    case = Case.objects.create(Name='Exam case generated 1', Caselist_id=1, Introduction='Test')
    q1 = Question.objects.create(Case=case, Type=Question.OPENTEXT, Text='Opentext', Order=1)
    q2 = Question.objects.create(Case=case, Type=Question.NUMERIC, Text='numeric', Order=2)
    q3 = Question.objects.create(Case=case, Type=Question.MULTIPLECHOICE, Text='multiple choice', Order=3)
    q4 = Question.objects.create(Case=case, Type=Question.LINE, Text='measure line', Order=4)
    QuestionItem.objects.create(Question=q3, Text='Choice 1', Order=1)
    QuestionItem.objects.create(Question=q3, Text='Choice 2', Order=2)
    QuestionItem.objects.create(Question=q3, Text='Choice 3', Order=3)
    for ans in range(count):
        user = User.objects.create(username='User'.join(str(ans)))
        UserCaseList.objects.create(User=user, CaseList_id=1, Status=UserCaseList.ACTIVE)
        ci = CaseInstance.objects.create(Case=case, User=user, Status=CaseInstance.ENDED)
        Answer.objects.create(CaseInstance=ci, Question=q1, AnswerText='Answer' + str(ans))
        Answer.objects.create(CaseInstance=ci, Question=q2, AnswerNumeric=ans)
        Answer.objects.create(CaseInstance=ci, Question=q3, AnswerNumeric=(ans % 3) + 1)
        answ = Answer.objects.create(CaseInstance=ci, Question=q4, AnswerText=str(ans + 1) + 'mm')
        AnswerAnnotation.objects.create(answer=answ, AnnotationJSON='["line", {"x1": "1.0", "y1": "1.0", "x2": "25.0", "y2": "25.0", "stroke": "green", "stroke-width": "3", "vector-effect": "non-scaling-stroke"}]', Slide_id=1, Length=ans + 1, LengthUnit='mm')
    return case


def create_case_with_all_question_types():
    case = Case.objects.create(Name='All question types', Caselist_id=1, Introduction='Test')
    for index, typechoice in enumerate(Question.question_type_choices):
        question = Question.objects.create(Case=case, Type=typechoice[0], Text=typechoice[1], Order=index)
        if question.Type == Question.MULTIPLECHOICE:
            for qi_index in range(3):
                QuestionItem.objects.create(Question=question, Text='Answer ' + str(qi_index), Order=qi_index)
    return case
