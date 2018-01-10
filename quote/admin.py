# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.utils.html import format_html
from quote.models import *

class LineItemInline(admin.TabularInline):
	model = LineItem

class ProductInline(admin.TabularInline):
	model = Product

class QuoteAdmin(admin.ModelAdmin):
	list_display = ['number', 'recipient', 'created', 'show_quote_url',]
	inlines = [LineItemInline, ]
	ordering = ('-created',)
	def show_quote_url(self, obj):
		print obj.id
		return format_html('<a target="_" href="/quote/{uuid}">{uuid}</a>', uuid=obj.id)
	show_quote_url.short_description = "Quote Page"

class ProductAdmin(admin.ModelAdmin):
	list_display = ('get_section_name', 'name', )
	list_filter = ('is_software','is_electric','is_gas','is_water','is_implementation','is_solver',)
	ordering = ('section__order', 'order_in_section',)
	def get_section_name(self, obj):
		return str(obj.section)
	get_section_name.short_description = 'Section'

class SectionAdmin(admin.ModelAdmin):
	inlines = [ProductInline, ]
	ordering = ('order',)

# Rename the admin site
admin.site.site_header = "PLEXOS by Energy Exemplar"

# Register your models here.
admin.site.register(Currency)
admin.site.register(TermIncrement)
admin.site.register(Section, SectionAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Recipient)
admin.site.register(Quote, QuoteAdmin)
admin.site.register(LineItem)
