# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from datetime import datetime, date, time, timedelta
from django.contrib.auth.models import User
import uuid

# Create your models here.
class Currency(models.Model):
	class Meta:
		verbose_name_plural = 'Currencies'
	name = models.CharField(max_length=45)
	abbr = models.CharField(max_length=6)
	symbol = models.CharField(max_length=6, default="$")
	conversion = models.DecimalField(max_digits=20, decimal_places=10, default=1)
	def __str__(self):
		return self.abbr
	
class TermIncrement(models.Model):
	name = models.CharField(max_length=40)
	text = models.CharField(max_length=40)
	prorata_percent = models.DecimalField(max_digits=6, decimal_places=2)
	def __str__(self):
		return self.name
		
class ProductLine(models.Model):
	name = models.CharField(max_length=20)
	logo = models.CharField(max_length=50, blank=True)
	is_v1 = models.BooleanField(default=False)
	is_v2 = models.BooleanField(default=False)
	overview = models.TextField(blank=True)
	def __str__(self):
		return self.name
	
class Section(models.Model):
	name = models.CharField(max_length=50)
	product_line = models.ForeignKey(ProductLine, default=0)
	note = models.TextField(blank=True)
	description = models.TextField(blank=True)
	order = models.IntegerField()
	def __str__(self):
		return '{}. {}'.format(self.order, self.name)
		
class Product(models.Model):
	section = models.ForeignKey(Section)
	order_in_section = models.IntegerField()
	year = models.IntegerField()
	name = models.CharField(max_length=50)
	quantity = models.IntegerField(default=1)
	price = models.DecimalField(max_digits=10, decimal_places=0)
	note = models.CharField(max_length=200, blank=True)
	is_software = models.BooleanField(default=True)
	is_training = models.BooleanField(default=False)
	is_onsite = models.BooleanField(default=False)
	is_implementation = models.BooleanField(default=False)
	is_data = models.BooleanField(default=False)
	is_engine = models.BooleanField(default=False)
	is_solver = models.BooleanField(default=False)
	is_electric = models.BooleanField(default=False)
	is_gas = models.BooleanField(default=False)
	is_water = models.BooleanField(default=False)
	is_usb = models.BooleanField(default=False)

	def is_old(self):
		return self.section.product_line.name in ['Old PLEXOS']

	def __str__(self):
		return '{} -- {} ({})'.format(self.section.name, self.name, self.year)
	
class Recipient(models.Model):
	fname = models.CharField(max_length=50, blank=True)
	lname = models.CharField(max_length=50, blank=True)
	salutation = models.CharField(max_length=10, blank=True)
	title = models.CharField(max_length=50, blank=True)
	company = models.CharField(max_length=50, blank=True)
	address = models.TextField(blank=True)
	email = models.EmailField()
	def __str__(self):
		if len(self.fname + self.lname + self.company) > 0:
			return '{} {} {} ({})'.format(self.salutation, self.fname, self.lname, self.company)
		else:
			return self.email


class Signature(models.Model):
	first_name = models.CharField(max_length=50, default="")
	last_name = models.CharField(max_length=50,default="")
	location = models.CharField(max_length=50,default="3013 Douglas Blvd, Suite 120\nRoseville CA 95661")
	title = models.CharField(max_length=50, blank=True)
	email = models.EmailField(default="")
	phone_number = models.CharField(max_length=50, blank=True)
	def __unicode__(self):
		return 'Signature: ' + self.first_name + ' ' + self.last_name
	
class AbstractQuote(models.Model):
	class Meta:
		abstract = True
		
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	created = models.DateTimeField(null=True,auto_now=True)
	days_of_validity = models.IntegerField(default=30)
	future_year = models.IntegerField(default=0)
	num_years = models.IntegerField(default=1)
	esc_percent = models.IntegerField(default=5)
	recipient = models.ForeignKey(Recipient, null=True, blank=True)
	currency = models.ForeignKey(Currency, default = 1)
	description = models.TextField(blank=True)
	pdf_file = models.FileField(blank=True)
	signature = models.ForeignKey(Signature, null=True)
	is_approved = models.BooleanField(default=False)
	def is_expired(self):
		return datetime.now() > self.created.replace(tzinfo=None) + timedelta(30)
	def get_multi_year_range(self):
		return range(1, self.num_years+1)
	def quote_url(self):
		return '/quote/{}'.format(id)
	def number(self):
		return '{:%Y%m%d%H%M%S}'.format(self.created)
	def valid(self):
		return self.created + timedelta(int(self.days_of_validity))
	def __str__(self):
		return '#{:%y%m%d%H%M%S} @{}'.format(self.created, self.recipient)
	
class Quote(AbstractQuote):
	class Meta:
		verbose_name = 'Quote (old pricing -- PLEXOS renewals)'
		verbose_name_plural = 'Quotes (old pricing -- PLEXOS renewals)'
	pass
	
class QuoteVersion2(AbstractQuote):
	class Meta:
		verbose_name_plural = 'Quotes (new pricing)'
		verbose_name = 'Quote (new pricing)'
	pass
	
class AbstractLineItem(models.Model):
	class Meta:
		abstract = True
		
	product = models.ForeignKey(Product)
	quantity = models.DecimalField(default=1, max_digits=5, decimal_places=2)
	is_override = models.BooleanField(default=False)
	override = models.DecimalField(default=0, max_digits=10, decimal_places=0)
	already = models.IntegerField(default=0)
	termincr = models.ForeignKey(TermIncrement)
	numterms = models.IntegerField(default=1)
	quote = models.ForeignKey(Quote)
	percent_discount = models.DecimalField(decimal_places=0, max_digits=3, default=0)

	def get_multi_year_subtotal(self):
		multi_year_subtotal = dict()
		for year in self.quote.get_multi_year_range(): 
			if self.product.is_software or self.product.is_training:
				multi_year_subtotal[year] = int(round(self.get_single_year_subtotal()* ((1+ float(self.quote.esc_percent)/100)**(year-1)), 0))
			elif year == 1:
				multi_year_subtotal[year] = self.get_single_year_subtotal()
			else:
				multi_year_subtotal[year] = 0
				
		return multi_year_subtotal

	def rate(self):
		sub = float(self.override) if self.is_override else float(self.product.price)
		sub *= float(self.numterms)
		sub *= float(self.termincr.prorata_percent)/100
		sub *= float(self.quote.currency.conversion)
		sub *= (1+float(self.quote.esc_percent)/100)**self.quote.future_year
		return int(round(sub, 0))
	
	def subtotal(self): 
		if self.quote.num_years == 1: 
			return self.get_single_year_subtotal()
		subtotal = 0
		for year, year_subtotal in self.get_multi_year_subtotal().iteritems(): 
			subtotal += year_subtotal
		return subtotal

	def get_single_year_subtotal(self):
		return int(self.rate()*(self.quantity-self.already))

	def discount(self):
		return int(round(float(self.subtotal())/100.0*float(self.percent_discount),0))
	def total(self):
		return self.subtotal() - self.discount()
	def is_discount(self):
		return self.percent_discount > 0
	def __str__(self):
		return '{} -- {}'.format(self.quote, self.description())

class LineItem(AbstractLineItem):
	product = models.ForeignKey(Product, limit_choices_to={'section__product_line__is_v1': 'True'})
	def description(self):
		if self.product.is_software:
			return '{}-{} license fee for {} {}'.format( \
				self.numterms, self.termincr.text.lower(), self.product.name, \
				'({} Paid)'.format(self.already) if self.already > 0 else '')
		else:
			return '{}'.format(self.product.name)
			
	pass

class LineItem2(AbstractLineItem):
	class Meta:
		verbose_name_plural = 'Line Item (new pricing)'
	product = models.ForeignKey(Product, limit_choices_to={'section__product_line__is_v2': 'True'})
	quote = models.ForeignKey(QuoteVersion2)
	def description(self):
		if self.product.is_software:
			return '{}-{} license fee for {} {}'.format( \
				self.numterms, self.termincr.text.lower(), self.product.note, \
				'({} Paid)'.format(self.already) if self.already > 0 else '')
		else:
			return '{}'.format(self.product.name)
			
	pass