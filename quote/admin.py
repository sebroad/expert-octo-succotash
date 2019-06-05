# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.utils.html import format_html
from quote.models import *

class LineItemInline(admin.TabularInline):
	model = LineItem
	fields = ['product','quantity','is_override','override','already','termincr','numterms','percent_discount']

class LineItem2Inline(admin.TabularInline):
	model = LineItem2
	fields = ['product','quantity','is_override','override','already','termincr','numterms','percent_discount']

class ProductInline(admin.TabularInline):
	model = Product

class BundledProductInline(admin.TabularInline):
	model = BundledProduct
	
class SectionInline(admin.TabularInline):
	model = Section
	
class QuoteAdmin(admin.ModelAdmin):
	list_display = ['number', 'recipient', 'created', 'show_quote_url',]
	inlines = [LineItemInline, ]
	ordering = ('-created',)
	def show_quote_url(self, obj):
		print obj.id
		return format_html('<a target="_" href="/quote/v1/{uuid}">{uuid}</a>', uuid=obj.id)
	show_quote_url.short_description = "Quote Page"

class Quote2Admin(admin.ModelAdmin):
	list_display = ['number', 'recipient', 'created', 'show_quote_url',]
	inlines = [LineItem2Inline, ]
	ordering = ('-created',)
	def show_quote_url(self, obj):
		print obj.id
		return format_html('<a target="_" href="/quote/v2/{uuid}">{uuid}</a>', uuid=obj.id)
	show_quote_url.short_description = "Quote Page"

class ProductAdmin(admin.ModelAdmin):
	list_display = ('get_product_name', 'note', 'get_product_line_name', 'get_section_name', )
	list_filter = ('is_software','is_electric','is_gas','is_water','is_implementation','is_solver',)
	ordering = ('section__order', 'order_in_section',)
	def get_product_name(self, obj):
		return '{}. {}'.format(obj.order_in_section, obj.name)
	get_product_name.short_description = 'Product'
	def get_product_line_name(self, obj):
		return str(obj.section.product_line.name)
	get_product_line_name.short_description = 'Product Line'
	def get_section_name(self, obj):
		return str(obj.section)
	get_section_name.short_description = 'Section'

class SectionAdmin(admin.ModelAdmin):
	list_display = ('name', 'get_product_line_name', )
	inlines = [ProductInline, ]
	ordering = ('order',)
	def get_product_line_name(self, obj):
		return obj.product_line.name
	get_product_line_name.short_description = 'Product Line'
	
class SignatureAdmin(admin.ModelAdmin):
	model = Signature

class ProductLineAdmin(admin.ModelAdmin):
	list_display = ('name','is_v1','is_v2',)
	inlines = [SectionInline, ]
	
# Rename the admin site
admin.site.site_header = "PLEXOS by Energy Exemplar"

# Register your models here.
admin.site.register(Currency)
admin.site.register(Signature, SignatureAdmin)
admin.site.register(ProductLine, ProductLineAdmin)
admin.site.register(TermIncrement)
admin.site.register(Section, SectionAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Recipient)
admin.site.register(Quote, QuoteAdmin)
admin.site.register(QuoteVersion2, Quote2Admin)
admin.site.register(BundledProduct)
