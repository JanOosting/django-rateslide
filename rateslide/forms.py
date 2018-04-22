from django.forms import ModelForm, Form, Field, CharField, IntegerField, TypedChoiceField, DateField, BooleanField
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.forms.widgets import HiddenInput, RadioSelect
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator

from .models import Question, CaseList, UserCaseList, QuestionItem, CaseBookmark, Case, CaseInstance, QuestionBookmark


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


class LineInput(HiddenInput):
    button_label = _('Measure')
    template_name = 'rateslide/forms/widgets/line_input.html'

    def button_name(self, name):
        """
        Given the name of the line input, return the name of the activation button
        input.
        """
        return name + '-button'

    def name2id(self, name):
        return 'id_' + name

    def length_name(self, name):
        """
        Given the name of the line input, return the name of the display input for the length
        input.
        """
        return name + '-length'

    def line_color(self):
        """
        Set the line color/ button color
        """
        return "green"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        button_name = self.button_name(name)
        button_id = self.name2id(button_name)
        length_name = self.length_name(name)
        length_id = self.name2id(length_name)
        context['widget'].update({
            'button_name': button_name,
            'button_id': button_id,
            'length_name': length_name,
            'length_id': length_id,
            'line_color': self.line_color(),
            'button_label': self.button_label,
        })
        return context


class LineField(Field):
    widget = LineInput


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
                # Add a list of bookmarks {pk, Text} to the value attribute of a hidden input
                field.widget.attrs.update({'question': question.pk, })
                field.initial = question.bookmarks()
            elif question.Type == Question.LINE:
                field = LineField(label=question.Text)

            if question.Required:
                tag = "R"
                field.required = True
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


class QuestionBookmarkForm(ModelForm):
    class Meta:
        model = QuestionBookmark
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(QuestionBookmarkForm, self).__init__(*args, **kwargs)
        self.fields['Question'].widget = HiddenInput()
        self.fields['Slide'].widget = HiddenInput()
        self.fields['CenterX'].widget = HiddenInput()
        self.fields['CenterY'].widget = HiddenInput()
        self.fields['Zoom'].widget = HiddenInput()
        self.fields['order'].widget = HiddenInput()
