.. _caselist:

CaseList
========

Purpose
-------

Case lists consist of cases. Each case contains slides or other images, and can contain questions.

Several types of case lists are possible.

**Show case list** Users don't have to be logged in. No questions are available within the cases

**Examination** Cases are all shown on case list case, and cases can be entered again.

**Inter observer** Cases are rated in random order. Answered cases can not be revised

**Case reporting** Show results of former Examination/Inter observer case lists



Model
-----

**Fields**

:**Name**: CharField
:**Slug**: AutoSlugField
:**Abstract**: TextField Short description of caselist. This can be entered as markdown
:**Description**: TextField Long description. This can be entered as markdown
:**InviteMail**: TextField Mail to invite users
:**WelcomeMail**: TextField Mail for accepted users
:**ReminderMail**: TextField Reminder mail after 5 days
:**Type**: CharField One of the types
:**ObserversPerCase**: PositiveIntegerField Used for type Inter observer variability
:**Owner**: ->Auth-User
:**VisibleForNonUsers**: BooleanField Is caselist shown on homepage for non-users
:**OpenForRegistration**: BooleanField Non-users can ask to join the caselist
:**SelfRegistration**: BooleanField Non-users do not have to be accepted by the owner
:**StartDate**: DateTimeField
:**EndDate**: DateTimeField
:**Status**: CharField
:**Users**: ->:ref:`usercaselist`->Auth-User

