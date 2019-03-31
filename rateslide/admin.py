from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse
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
    fields = (('Order', 'Required', 'Type', 'Text', 'CorrectAnswer', ), )
    inlines = [CaseQuestionItemInline, ]
    extra = 2

    
class CaseAdmin(NestedModelAdmin):
    fieldsets = [
        (None, {'fields': ('Caselist', ('Order', 'Name', ), 'Introduction', 'Report', )}), ]
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
            return HttpResponseRedirect(reverse('rateslide:caselistadmin', args=(obj.Caselist.Slug,)))
        else:
            return super(CaseAdmin, self).response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if '_continue' not in request.POST:
            return HttpResponseRedirect(reverse('rateslide:caselistadmin', args=(obj.Caselist.Slug, )))
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
case_admin_site.register(Case, CaseAdmin)


class NewUserAdmin(UserAdmin):
    actions = ['delete_inactive_anonymous_users']

    def delete_inactive_anonymous_users(self, request, queryset):
        anonymous_users = User.objects.filter(first_name='Anonymous', last_name='User')
        for user in anonymous_users:
            ucls = UserCaseList.objects.filter(User=user)
            answered_cases = 0
            for ucl in ucls:
                answered_cases += ucl.case_count_completed()
            if answered_cases == 0:
                user.delete()


admin.site.unregister(User)
admin.site.register(User, NewUserAdmin)
