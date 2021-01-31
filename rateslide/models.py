from copy import deepcopy
from random import choice

from django.db import models, transaction
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import m2m_changed, post_save
from invitation.models import InvitationKey
from django_extensions.db.fields import AutoSlugField

from histoslide.models import Slide, SlideAnnotation, SlideBookmark

from .utils import send_usercaselist_mail


class CaseList(models.Model):
    OBSERVER = 'O'
    CASEREPORT = 'C'
    EXAMINATION = 'E'
    SHOWCASE = 'S'
    caselist_type_choices = (
        (OBSERVER, 'Observer variability'),
        (CASEREPORT, 'Case reporting'),
        (EXAMINATION, 'Examination'),
        (SHOWCASE, 'Show case'),
    )
    Name = models.CharField(max_length=50)
    Slug = AutoSlugField(populate_from='Name', unique=True)
    Abstract = models.TextField()      # This can be entered as markdown
    Description = models.TextField()   # This can be entered as markdown
    InviteMail = models.TextField()
    WelcomeMail = models.TextField()
    ReminderMail = models.TextField()
    Type = models.CharField(max_length=1, choices=caselist_type_choices)
    ObserversPerCase = models.PositiveIntegerField(default=0, help_text='Enter 0 to have all cases seen by observers')
    Owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="Owner")
    VisibleForNonUsers = models.BooleanField(
        help_text='Case shows up on main screen when a user is not assigned to this case list', default=False)
    OpenForRegistration = models.BooleanField(help_text='A user can admit himself to this case list', default=False)
    SelfRegistration = models.BooleanField(
        help_text='If false, the owner must accept the admittance of a user to the case list', default=False)
    StartDate = models.DateTimeField(auto_now_add=True)
    EndDate = models.DateTimeField(null=True, blank=True)
    Status = models.CharField(max_length=10, blank=True)
    Users = models.ManyToManyField(User, through='UserCaseList')
    SlideBase = models.CharField(max_length=200, blank=True)
    
    def cases(self):
        # get a set of case ids for this caselist
        return set(Case.objects.filter(Caselist=self).values_list('pk', flat=True))

    def case_count(self):
        return len(self.cases())

    def user_count(self):
        return UserCaseList.objects.filter(CaseList=self).count()
    
    def cases_total(self, user_id):
        return self.cases().difference(self.cases_skipped(user_id))

    def case_count_total(self, user_id):
        return len(self.cases_total(user_id))

    def cases_completed(self, user_id):
        # get a set of case ids that a user has completed
        user = User.objects.get(pk=user_id)
        return set(CaseInstance.objects.filter(User=user, Status='E',
                                               Case__in=self.cases()).values_list('Case', flat=True))

    def case_count_completed(self, user_id):
        return len(self.cases_completed(user_id))
    
    def cases_skipped(self, user_id):
        # get a set of case ids that a user has completed
        user = User.objects.get(pk=user_id)
        return set(CaseInstance.objects.filter(User=user, Status='S',
                                               Case__in=self.cases()).values_list('Case', flat=True))

    def case_count_skipped(self, user_id):
        return len(self.cases_skipped(user_id))

    def cases_todo(self, user_id):
        return self.cases().difference(self.cases_completed(user_id)).difference(self.cases_skipped(user_id))

    def get_next_case(self, user_id):
        # Select a case that has not been scored yet
        if self.ObserversPerCase == 0:
            # Select a list of cases with the lowest Order value still to be scored
            cases = Case.objects.filter(Caselist=self).exclude(caseinstance__User=user_id).order_by('Order')
            if cases:
                cases = cases.filter(Order=cases[0].Order)
                if self.Type == self.OBSERVER:
                    return choice(list(cases.values_list('pk', flat=True)))
                else:
                    return cases[0].pk
            else:
                return -1
        else:
            # Limit number of assessments per case
            # count the number of complete caseinstance for each case
            cases = Case.objects.filter(Caselist=self).\
                exclude(caseinstance__User=user_id).annotate(models.Count('caseinstance')).\
                order_by('caseinstance__count')
            if cases:
                # Select from the cases that have been assessed least
                cases = cases.filter(caseinstance__count=cases[0].caseinstance__count)
                return choice(list(cases.values_list('pk', flat=True)))
            else:
                return -1

    def evaluation(self, user_id):
        user = User.objects.get(pk=user_id)
        caseinstances = CaseInstance.objects.filter(User=user, Status='E',
                                               Case__in=self.cases()).values_list('Case', flat=True)
        answers = Answer.objects.filter(CaseInstance__in=caseinstances.values('id'))
        graded_answers = 0
        correct_answers = 0
        for answer in answers:
            grade = answer.grade()
            if grade == Answer.ERROR or grade == Answer.CORRECT:
                graded_answers += 1
                if grade == Answer.CORRECT:
                    correct_answers += 1
        if graded_answers > 0:
            return f'{correct_answers} of {graded_answers}'
        else:
            return ''


    def __str__(self):
        return self.Name


class Case(models.Model):
    Name = models.CharField(max_length=50)
    Caselist = models.ForeignKey(CaseList, on_delete=models.CASCADE)
    Order = models.IntegerField(default=0)
    Introduction = models.TextField()
    Slides = models.ManyToManyField(Slide, through='CaseSlide')
    Report = models.TextField(blank=True)

    class Meta:
        ordering = ['Order', 'Name']

    def __str__(self):
        return self.Name
    
    @transaction.atomic
    def copy_case(self):
        new_case = deepcopy(self)
        new_case.id = None
        new_case.Name += 'c'
        new_case.save()
        # Now copy the attached questions
        questions = Question.objects.filter(Case=self.pk)
        for question in questions:
            question.question_copy(new_case)
        # Copy slides
        for caseslide in CaseSlide.objects.filter(Case=self):
            new_caseslide = CaseSlide(Case=new_case, Slide=caseslide.Slide, order=caseslide.order)
            new_caseslide.save()
        return new_case

    
class CaseInstance(models.Model):
    OPEN = 'O'
    SKIPPED = 'S'
    ENDED = 'E'
    status_choices = (
        (OPEN, 'Open'),
        (SKIPPED, 'Skipped'),
        (ENDED, 'Ended'),
    )
    Case = models.ForeignKey(Case, on_delete=models.CASCADE)
    User = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    Status = models.CharField(max_length=1, choices=status_choices)
    StartTime = models.DateTimeField(auto_now_add=True)
    EndTime = models.DateTimeField(auto_now=True)


class Question(models.Model):
    MULTIPLECHOICE = 'M'
    OPENTEXT = 'O'
    NUMERIC = 'N'
    DATE = 'D'
    REMARK = 'R'
    LINE = 'L'

    question_type_choices = (
        (MULTIPLECHOICE, 'MultipleChoice'),
        (OPENTEXT, 'Open text'),
        (NUMERIC, 'Numeric'),
        (DATE, 'Date'),
        (REMARK, 'Remark'),
        (LINE, 'Line'),)
    Case = models.ForeignKey(Case, on_delete=models.CASCADE)
    Type = models.CharField(max_length=1, choices=question_type_choices)
    Order = models.IntegerField()
    Text = models.CharField(max_length=200)
    Required = models.BooleanField(default=False)
    CorrectAnswer = models.CharField(max_length=40, blank=True)

    class Meta:
        ordering = ['Order']

    def __str__(self):
        return u'%d %s %s' % (self.Order, self.required_char(), self.Text)

    def required_char(self):
        if self.Required:
            return u'*'
        else:
            return u' '

    def question_copy(self, new_case):
        new_question = deepcopy(self)
        new_question.id = None
        new_question.Case = new_case
        new_question.save()
        # Copy the choices for a multiple choice question
        if new_question.Type == Question.MULTIPLECHOICE:
            questionitems = QuestionItem.objects.filter(Question=self.pk)
            for questionitem in questionitems:
                questionitem.questionitem_copy(new_question)

    def bookmarks(self):
        return list(QuestionBookmark.objects.filter(Question=self).order_by('order').values('pk', 'Text'))

    def fieldid(self):
        return 'question_%s_%s_%s' % ('R' if self.Required else 'F', self.Type, self.id)

    def correcttext(self):
        if self.Type == Question.MULTIPLECHOICE:
            mc_choice = QuestionItem.objects.filter(Question=self, Order=self.CorrectAnswer)
            if mc_choice.count() == 1:
                return mc_choice[0].Text
            else:
                return ''
        else:
            return self.CorrectAnswer


# Items for multiple choice questions
class QuestionItem(models.Model):
    Question = models.ForeignKey(Question, on_delete=models.CASCADE)
    Order = models.IntegerField()
    Text = models.CharField(max_length=200)

    class Meta:
        ordering = ['Order']

    def questionitem_copy(self, new_question):
        new_questionitem = deepcopy(self)
        new_questionitem.id = None
        new_questionitem.Question = new_question
        new_questionitem.save()

    
class Answer(models.Model):
    CORRECT = 'C'
    ERROR = 'E'
    NOEVAL = 'S'

    CaseInstance = models.ForeignKey(CaseInstance, on_delete=models.CASCADE)
    Question = models.ForeignKey(Question, on_delete=models.CASCADE)
    AnswerNumeric = models.IntegerField(default=0)
    AnswerText = models.TextField(blank=True)

    def textvalue(self):
        if self.Question.Type == Question.NUMERIC:
            return self.AnswerNumeric
        elif self.Question.Type == Question.MULTIPLECHOICE:
            mc_choice = QuestionItem.objects.filter(Question=self.Question, Order=self.AnswerNumeric)
            if mc_choice.count() == 1:
                return mc_choice[0].Text
            else:
                return ''
        elif self.Question.Type == Question.LINE:
            if hasattr(self, 'answerannotation'):
                annotation = loads(answer.answerannotation.AnnotationJSON)
                return dumps({'length': answer.answerannotation.Length,
                                                         'length_unit': answer.answerannotation.LengthUnit,
                                                         'slideid': answer.answerannotation.Slide_id,
                                                         'annotation': annotation})
            else:
                return ''
        else:
            return self.AnswerText

    def grade(self):
        if self.Question.CorrectAnswer == '':
            return Answer.NOEVAL
        elif self.Question.CorrectAnswer == self.AnswerText or self.Question.CorrectAnswer == str(self.AnswerNumeric):
            return Answer.CORRECT
        else:
            return Answer.ERROR



class AnswerAnnotation(SlideAnnotation):
    answer = models.OneToOneField(Answer, on_delete=models.CASCADE)


class UserCaseList(models.Model):
    ACTIVE = 'A'
    PENDING = 'P'
    COMPLETE = 'C'
    NONE = 'N'  # can be generated when a user is not in a caselist
    status_choices = (
        (ACTIVE, 'Active'),
        (PENDING, 'Pending'),
        (COMPLETE, 'Complete')
    )
    User = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    CaseList = models.ForeignKey(CaseList, on_delete=models.CASCADE)
    Status = models.CharField(max_length=1, choices=status_choices, default=ACTIVE)
    StartTime = models.DateTimeField(auto_now_add=True)
    EndTime = models.DateTimeField(null=True, blank=True)

    def cases_completed(self):
        # get a set of case ids that a user has completed
        return self.CaseList.cases_completed(self.User.id)

    def case_count_completed(self):
        return len(self.cases_completed())

    def cases_todo(self):
        return self.CaseList.cases_todo(self.User.id)

    def case_count_todo(self):
        return len(self.cases_todo())

    def cases_total(self):
        return self.CaseList.cases_total(self.User.id)

    def case_count_total(self):
        return len(self.cases_total())

    def __str__(self):
        return u'%s %s' % (self.User.username, self.CaseList.Name)


class CaseSlide(models.Model):
    Case = models.ForeignKey(Case, on_delete=models.CASCADE)
    Slide = models.ForeignKey(Slide, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return u'%s %s' % (self.Case.Name, self.Slide.Name)


class CaseBookmark(SlideBookmark):
    Case = models.ForeignKey(Case, on_delete=models.CASCADE)


class QuestionBookmark(SlideBookmark):
    Question = models.ForeignKey(Question, on_delete=models.CASCADE)


# Connect Users with Caselist when they respond to invitations
class CaseListInvitation(models.Model):
    Caselist = models.ForeignKey(CaseList, on_delete=models.CASCADE)
    Invitation = models.ForeignKey(InvitationKey, on_delete=models.CASCADE)


def registrant_m2m_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    """Connect to caselist When a registration is made using this key.
    """
    # Check registrant against caselists
    if action == "post_add":
        newusers = User.objects.filter(pk__in=pk_set)
        for newuser in newusers:
            caselistinvitations = CaseListInvitation.objects.filter(Invitation=instance)
            for caselistinvitation in caselistinvitations:
                ucl, created = UserCaseList.objects.get_or_create(User=newuser, CaseList=caselistinvitation.Caselist,
                                                                  defaults={'Status': UserCaseList.ACTIVE})
                send_usercaselist_mail(ucl, 'welcome')


m2m_changed.connect(registrant_m2m_changed, sender=InvitationKey.registrant.through)


def caselist_post_save(sender, instance, created, raw, using, **kwargs):
    """ Add the owner to the caselistusers
    """
    if not raw:
        ucl, created = UserCaseList.objects.get_or_create(User=instance.Owner, CaseList=instance,
                                                                  defaults={'Status': UserCaseList.ACTIVE})

post_save.connect(caselist_post_save, sender=CaseList)
