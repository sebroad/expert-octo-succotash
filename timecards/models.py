# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
import django.utils.timezone

# Create your models here.
class Resource(models.Model):
	username = models.OneToOneField(User, on_delete=models.CASCADE)
	phone = models.CharField(max_length=15)
	cell_phone = models.CharField(max_length=15)
	SandPoint = 'SP'
	SaltLakeCity = 'SLC'
	Portland = 'PDX'
	Sacramento = 'SAC'
	Columbus = 'COL'
	OFFICE_CHOICES = ( \
		(SandPoint, 'Sand Point'), \
		(SaltLakeCity, 'Salt Lake City'), \
		(Portland, 'Portland'), \
		(Sacramento, 'Sacramento'), \
		(Columbus, 'Columbus'), \
		)
	office = models.CharField( \
		max_length=3, \
		choices=OFFICE_CHOICES, \
		default=Sacramento, \
		)

	full_name = models.CharField(max_length=40,default='')
	def get_full_name(self):
		return '{} {}'.format(self.username.first_name, self.username.last_name)
	def __str__(self):
		return self.get_full_name()
	
class Recipient(models.Model):
	contact = models.CharField(max_length=100) 
	company = models.CharField(max_length=100)
	address = models.TextField()
	email = models.EmailField()
	po_number = models.CharField(max_length=100, blank=True)
	def __str__(self):
		return '{} {} ({})'.format(self.contact, self.company, self.po_number)
		pass
	
class BillingMethod(models.Model):
	name = models.CharField(max_length=100)
	is_billed = models.BooleanField(default=False)
	is_monthly = models.BooleanField(default=False)
	is_fixed = models.BooleanField(default=False)
	is_on_approval = models.BooleanField(default=False)
	def __str__(self):
		return self.name
	
class ProjectGroup(models.Model):
	name = models.CharField(max_length=20)
	def __str__(self):
		return self.name
	
class Project(models.Model):
	project_name = models.CharField(max_length=100)
	project_group = models.ForeignKey(ProjectGroup, default=1, on_delete=models.CASCADE)
	recipient = models.ForeignKey(Recipient, null=True, blank=True, on_delete=models.CASCADE)
	billing_method = models.ForeignKey(BillingMethod, default=1, on_delete=models.CASCADE)
	budget = models.DecimalField(default=0.0, max_digits=10, decimal_places=0)
	def __str__(self):
		return self.project_name
	pass
	
class ProjectResource(models.Model):
	resource = models.ForeignKey(Resource, related_name='projres', on_delete=models.CASCADE)
	project = models.ForeignKey(Project, related_name='projres', on_delete=models.CASCADE)
	billing_rate = models.DecimalField(max_digits=8,decimal_places=0)
	title = models.CharField(max_length=40)
	def __str__(self):
		return '{} ({})'.format(self.resource.full_name, self.project.project_name)

class Phase(models.Model):
	project = models.ForeignKey(Project, on_delete=models.CASCADE)
	phase_name = models.CharField(max_length=100)
	def __str__(self):
		return '{} --> {}'.format(self.project.name, self.phase_name)
	
class TimeSheet(models.Model):
	created = models.DateTimeField(auto_now=True)
	name = models.CharField(max_length=100)
	resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
	def __str__(self):
		return self.name
	
class TimeCard(models.Model):
	created = models.DateTimeField(auto_now=True)
	date_of_work = models.DateField()
	project = models.ForeignKey(Project, on_delete=models.CASCADE)
	timesheet = models.ForeignKey(TimeSheet, null=True, on_delete=models.CASCADE)
	phase = models.ForeignKey(Phase,null=True,blank=True, on_delete=models.CASCADE)
	hours = models.DecimalField(max_digits=5, decimal_places=2)
	comment = models.TextField(max_length=300)
	def billing_rate(self):
		if self.project.billing_method.is_billed:
			pr = self.timesheet.resource.projres.filter(project__id=self.project.id)
			return 0.0 if len(pr) == 0 else pr[0].billing_rate
		else:
			return 0.0
	def total(self):
		if self.project.billing_method.is_billed:
			return float(self.billing_rate()) * float(self.hours)
		else:
			return 0.0
	def __str__(self):
		return '{:%Y-%m-%d} {}'.format(self.date_of_work, self.project.project_name)
	
