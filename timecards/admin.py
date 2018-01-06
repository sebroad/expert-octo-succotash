# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import *
from django.utils.html import format_html
from django.forms import TextInput

from django.forms import BaseInlineFormSet

class TimeCardInline(admin.TabularInline):
	model = TimeCard
	ordering = ('date_of_work', )
	
class TimeSheetAdmin(admin.ModelAdmin):
	inlines = [ TimeCardInline, ]
	list_display = ('name', 'resource', 'show_link',)
	def show_link(self, obj):
		return format_html('<a target="_" href="/timecards/ts/{name}">{name}</a>', name=obj.name)
	show_link.short_description = "TimeSheet Link"
	
class ProjectAdmin(admin.ModelAdmin):
	list_display = ('project_name', 'project_group', 'show_link', )
	def show_link(self, obj):
		return format_html('<a target="_" href="/timecards/project/{name}">{name}</a>', name=obj.project_name)
	show_link.short_description = "Project Link"
	
class ResourceAdmin(admin.ModelAdmin):
	list_display = ('full_name', 'show_link', )
	def show_link(self, obj):
		return format_html('<a target="_" href="/timecards/resource/{name}">{name}</a>', name=obj.username.username)
	show_link.short_description = "Resource Link"
	
# Register your models here.
admin.site.register(ProjectGroup)
admin.site.register(Resource, ResourceAdmin)
admin.site.register(ProjectResource)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Recipient)
admin.site.register(BillingMethod)
admin.site.register(Phase)
admin.site.register(TimeCard)
admin.site.register(TimeSheet, TimeSheetAdmin)