# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from .models import *
from django import forms

class LeaveDayInline(admin.TabularInline):
	model = LeaveDay

def approve_request(modeladmin, request, queryset):
	for leave in queryset:
		if not leave.is_approved():
			obj = LeaveApproval()
			obj.approver = Resource.objects.filter(username=request.user)[0]
			obj.request = leave
			obj.save()
		
class ApprovedFilter(SimpleListFilter):
    title = 'Is Approved?' # or use _('country') for translated title
    parameter_name = 'is_approved'

    def lookups(self, request, model_admin):
        countries = set([c.country for c in model_admin.model.objects.all()])
        return [(c.id, c.name) for c in countries]

    def queryset(self, request, queryset):
        if self.value() == 'AFRICA':
            return queryset.filter(country__continent='Africa')
        if self.value():
            return queryset.filter(country__id__exact=self.value())
	
class LeaveRequestAdmin(admin.ModelAdmin):
	list_display = ['show_leave_id', 'office', 'application_date', 'is_approved', 'show_leave_req_url',]
	#list_filter = ['is_approved',]
	
	inlines = [LeaveDayInline, ]
	actions = [approve_request, ]
	ordering = ('-application_date',)
	
	def show_leave_id(self, obj):
		return str(obj)
	show_leave_id.short_description = "Leave Request"
	
	def show_leave_req_url(self, obj):
		return format_html('<a target="_" href="/leavereq/{uuid}">{uuid}</a>', uuid=obj.id)
	show_leave_req_url.short_description = "Printable Leave Request"
	
	def is_approved(self, obj):
		return 'Yes' if obj.is_approved() else 'No'
	

class LeaveApprovalAdmin(admin.ModelAdmin):
	list_display = ['show_leave_id', 'approval_timestamp', 'show_leave_req_url',]
	ordering = ('-approval_timestamp',)
	
	def show_leave_req_url(self, obj):
		return format_html('<a target="_" href="/leavereq/{uuid}">{uuid}</a>', uuid=obj.request.id)
	show_leave_req_url.short_description = "Printable Leave Approval"
	def show_leave_id(self, obj):
		return str(obj)
	show_leave_id.short_description = "Leave Approval"	
	

# Register your models here.
admin.site.register(LeaveRequest, LeaveRequestAdmin)
admin.site.register(LeaveApproval, LeaveApprovalAdmin)

