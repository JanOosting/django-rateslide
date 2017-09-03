from django.forms import ModelForm, Form, CharField, IntegerField, TypedChoiceField, DateField, BooleanField
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.forms.widgets import HiddenInput, RadioSelect
from django.core.validators import MinValueValidator

from .models import Question, CaseList, UserCaseList, QuestionItem, CaseBookmark, Case, CaseInstance


class CaseListForm(ModelForm):
    class Meta:
        model = CaseList
        fields = ['Name', 'Abstract', 'Description', 'Type', 'ObserversPerCase', 'VisibleForNonUsers',
                  'OpenForRegistration', 'SelfRegistration', 'EndDate', 'WelcomeMail', 'InviteMail', 'ReminderMail']


class UserCaseListSelectForm(ModelForm):
    selected = BooleanField(initial=False, required=False)
    
    class Meta:
        model = UserCaseList
        fields = '__all__'

UserCaseListSelectFormSet = modelformset_factory(UserCaseList, form=UserCaseListSelectForm, extra=0)


class TempUserForm(Form):
    id = IntegerField()
    selected = BooleanField(required=False)

tempUserFormSet = formset_factory(TempUserForm)


class CaseInstancesSelectForm(ModelForm):
    selected = BooleanField(initial=False, required=False)

    class Meta:
        model = CaseInstance
        fields = '__all__'

CaseInstancesSelectFormSet = modelformset_factory(CaseInstance, form=CaseInstancesSelectForm, extra=0)


class CasesSelectForm(ModelForm):
    selected = BooleanField(initial=False, required=False)

    class Meta:
        model = Case
        fields = '__all__'

CasesSelectFormSet = modelformset_factory(Case, form=CasesSelectForm, extra=0)


class QuestionForm(Form):
    def __init__(self, questions, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        for question in questions:
                
            if question.Type == Question.OPENTEXT:
                field = CharField(label=question.Text)
            elif question.Type == Question.NUMERIC: 
                field = IntegerField(label=question.Text)
            elif question.Type == Question.MULTIPLECHOICE: 
                field = TypedChoiceField(
                    label=question.Text,
                    choices=QuestionItem.objects.filter(Question=question.id).values_list('Order', 'Text'),
                    coerce=int, widget=RadioSelect(attrs={'class': 'form-button-radio'}))
            elif question.Type == Question.DATE: 
                field = DateField(label=question.Text)
            elif question.Type == Question.REMARK:
                field = CharField(label=question.Text, widget=HiddenInput)

            if question.Required:
                tag = "R"
                field.required = True
                if question.Type == Question.MULTIPLECHOICE:
                    field.validators = [MinValueValidator(1)]
            else:
                tag = "F"
                field.required = False

            self.fields['question_%s_%s_%s' % (tag, question.Type, question.id)] = field   


class CaseBookmarkForm(ModelForm):
    
    class Meta:
        model = CaseBookmark
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super(CaseBookmarkForm, self).__init__(*args, **kwargs)
        self.fields['Case'].widget = HiddenInput()
        self.fields['Slide'].widget = HiddenInput()
        self.fields['CenterX'].widget = HiddenInput()
        self.fields['CenterY'].widget = HiddenInput()
        self.fields['Zoom'].widget = HiddenInput()
        self.fields['order'].widget = HiddenInput()
