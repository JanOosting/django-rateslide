from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from nested_inlines.admin import NestedModelAdmin, NestedStackedInline, NestedTabularInline

from .models import Case, CaseList, Question, QuestionItem, UserCaseList, CaseSlide, CaseBookmark

admin.site.register(CaseList)
admin.site.register(UserCaseList)


class UserCaseListInline(admin.TabularInline):
    """ Bind CaseLists to UserProfile
    """
    model = UserCaseList
    extra = 1
    

class QuestionItemInline(admin.TabularInline):
    """ Enable editing of multiple choice items for questions
    """
    model = QuestionItem
    extra = 4


class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ('Order', 'Case', 'Type', 'Required', 'Text')}), ]
    list_filter = ('Case',)
    radio_fields = {"Type": admin.VERTICAL}
    inlines = [QuestionItemInline]

admin.site.register(Question, QuestionAdmin)


class CaseSlideInline(NestedTabularInline):
    """Bind questions to cases
    """
    model = CaseSlide
    extra = 1


class CaseBookmarkInline(NestedTabularInline):
    model = CaseBookmark
    extra = 1


class CaseQuestionItemInline(NestedTabularInline):
    model = QuestionItem
    extra = 1


class CaseQuestionInline(NestedStackedInline):
    model = Question
    inlines = [CaseQuestionItemInline, ]
    extra = 2

    
class CaseAdmin(NestedModelAdmin):
    fieldsets = [
        (None, {'fields': ('Caselist', 'Name', 'Introduction', 'Report', 'Order')}), ]
    inlines = [CaseSlideInline, CaseBookmarkInline, CaseQuestionInline, ]
    actions = ['copy_cases']

    def copy_cases(self, request, queryset):
        cases_copied = 0
        for case in queryset:
            case.copy_case()
            cases_copied += 1
        if cases_copied == 1:
            message_bit = "1 case was"
        else:
            message_bit = "%s cases were" % cases_copied
        self.message_user(request, "%s successfully copied." % message_bit)
        
    def response_add(self, request, obj, post_url_continue="../%s/"):
        if '_continue' not in request.POST:
            return HttpResponseRedirect(reverse('rateslide:caselistadmin', args=(obj.Caselist.id,)))
        else:
            return super(CaseAdmin, self).response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if '_continue' not in request.POST:
            return HttpResponseRedirect(reverse('rateslide:caselistadmin', args=(obj.Caselist.id, )))
        else:
            return super(CaseAdmin, self).response_change(request, obj)    


# Use the admin view for cases for caselist owners
# http://www.tryolabs.com/Blog/2012/06/18/django-administration-interface-non-staff-users/
class CaseAdminSite(AdminSite):
    # Anything we wish to add or override
    login_form = AuthenticationForm
    
    def has_permission(self, request):
        # Removed check for is_staff.
        return request.user.is_active

case_admin_site = CaseAdminSite(name='caseadm')
# Run user_admin_site.register() for each model we wish to register

case_admin_site.register(Case, CaseAdmin)
