# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.utils.html import format_html
from .models import *
from django import forms

class LeaveDayInline(admin.TabularInline):
	model = LeaveDay

class LeaveRequestAdmin(admin.ModelAdmin):
	list_display = ['show_leave_id', 'office', 'application_date', 'show_leave_req_url',]
	inlines = [LeaveDayInline, ]
	ordering = ('-application_date',)
	def show_leave_req_url(self, obj):
		return format_html('<a target="_" href="/leavereq/{uuid}">{uuid}</a>', uuid=obj.id)
	show_leave_req_url.short_description = "Printable Leave Request"
	def show_leave_id(self, obj):
		return str(obj)
	show_leave_id.short_description = "Leave Request"


# Rename the admin site
admin.site.site_header = "PLEXOS by Energy Exemplar"

# Register your models here.
admin.site.register(LeaveRequest, LeaveRequestAdmin)
admin.site.register(LeaveApproval)

