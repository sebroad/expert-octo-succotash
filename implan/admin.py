from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from .models import *
from django import forms
from datetime import datetime

class DeploymentInline(admin.TabularInline):
    exclude = ['created_by', 'created_at', 'modified_by', 'modified_at', ]
    model = Deployment
    extra = 1

class CustomizationInline(admin.TabularInline):
    exclude = ['created_by', 'created_at', 'modified_by', 'modified_at', ]
    model = Customization
    extra = 1

class ModelBuildingInline(admin.TabularInline):
    exclude = ['created_by', 'created_at', 'modified_by', 'modified_at', ]
    model = ModelBuilding
    extra = 3

class AutomationInline(admin.TabularInline):
    exclude = ['created_by', 'created_at', 'modified_by', 'modified_at', ]
    model = Automation
    extra = 1

class SystemIntegrationInline(admin.TabularInline):
    exclude = ['created_by', 'created_at', 'modified_by', 'modified_at', ]
    model = SystemIntegration
    extra = 1

class ProductTrainingInline(admin.TabularInline):
    exclude = ['created_by', 'created_at', 'modified_by', 'modified_at', ]
    model = ProductTraining
    extra = 1

class HandoverWorkshopInline(admin.TabularInline):
    exclude = ['created_by', 'created_at', 'modified_by', 'modified_at', ]
    model = HandoverWorkshop
    extra = 1

class ValidationInline(admin.TabularInline):
    exclude = ['created_by', 'created_at', 'modified_by', 'modified_at', ]
    model = Validation
    extra = 1

class DetailedPlanningInline(admin.TabularInline):
    exclude = ['created_by', 'created_at', 'modified_by', 'modified_at', ]
    model = DetailedPlanningPhase
    extra = 1

class GoLiveInline(admin.TabularInline):
    exclude = ['created_by', 'created_at', 'modified_by', 'modified_at', ]
    model = GoLive
    extra = 1

class ImplementationPlanAdmin(admin.ModelAdmin):
    ordering = ['-modified_at']
    list_display = ['project_name', 'project_cost', 'ee_effort', 'show_account_link', 'show_plan_link', 'show_gantt_link', 'download_gantt_link', ]
    list_filter = ['group__company__name', ]
    exclude = ['created_by', 'created_at', 'modified_by', 'modified_at', ]
    inlines = [DeploymentInline, ProductTrainingInline, DetailedPlanningInline, ModelBuildingInline, CustomizationInline, \
        SystemIntegrationInline, AutomationInline, ValidationInline, HandoverWorkshopInline, GoLiveInline, ]
    def show_gantt_link(self, obj): return format_html('<a target="_" href="/implan/v1/gantt/{id}">{name} Data</a>', id=obj.id, name=obj.project_name, )
    def download_gantt_link(self, obj): return format_html('<a target="_" href="/implan/v1/gantt/{id}" download="{name}{timestamp}.csv">{name} Download</a>', id=obj.id, name=obj.project_name, timestamp=datetime.now().isoformat())
    def show_plan_link(self, obj): return format_html('<a target="_" href="/implan/v1/{id}">Project Overview</a>', id=obj.id)
    def show_account_link(self, obj): return format_html('<a target="_" href="{link}">{company}</a>', link=obj.group.company.sfdc, company=obj.group.company.name)

class GroupAdmin(admin.ModelAdmin):
    list_display = ['company', 'name', 'contact', ]
    exclude = ['created_by', 'created_at', 'modified_by', 'modified_at', ]

class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_sfdc_link', ]
    exclude = ['created_by', 'created_at', 'modified_by', 'modified_at', ]
    def get_sfdc_link(self, obj): return format_html('<a target="_" href="{link}">{company} Salesforce Link</a>', link=obj.sfdc, company=obj.name)

class UseCaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', ]
    exclude = ['created_by', 'created_at', 'modified_by', 'modified_at', ]

class UniqueBusinessValueDriverAdmin(admin.ModelAdmin):
    list_display = ['name', 'bene', ]
    exclude = ['created_by', 'created_at', 'modified_by', 'modified_at', ]

class TechnicalDifferentiatorsAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'created_at', 'modified_by', 'modified_at', ]

class CommercialDatasetsAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_nodal', ]
    exclude = ['created_by', 'created_at', 'modified_by', 'modified_at', ]

class TaskAdmin(admin.ModelAdmin):
    list_display = ['get_project_name', 'outline', 'name', 'start_date', 'end_date', 'cost', ]
    exclude = ['created_by', 'created_at', 'modified_by', 'modified_at', ]
    list_filter = ['implan__project_name', 'implan__group__company__name', 'modified_by', 'created_by']
    ordering = ['-implan__modified_at', 'outline']
    list_display_links = ['outline']
    list_editable = ['name', 'start_date', 'end_date', 'cost']
    def get_project_name(self, obj): return obj.implan.project_name
    get_project_name.short_description = 'Project Name'

# Register your models here.
admin.site.register(ImplementationPlan, ImplementationPlanAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(UseCase, UseCaseAdmin)
admin.site.register(UniqueBusinessValueDriver, UniqueBusinessValueDriverAdmin)
admin.site.register(TechnicalDifferentiators, TechnicalDifferentiatorsAdmin)
admin.site.register(CommercialDatasets, CommercialDatasetsAdmin)
admin.site.register(Task, TaskAdmin)
