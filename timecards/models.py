# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
import django.utils.timezone

# Create your models here.
class Resource(models.Model):
	username = models.OneToOneField(User)
	full_name = models.CharField(max_length=100)
	def __str__(self):
		return self.full_name
	
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
	project_group = models.ForeignKey(ProjectGroup, default=1)
	recipient = models.ForeignKey(Recipient, null=True, blank=True)
	billing_method = models.ForeignKey(BillingMethod, default=1)
	budget = models.DecimalField(default=0.0, max_digits=10, decimal_places=0)
	def __str__(self):
		return self.project_name
	pass
	
class ProjectResource(models.Model):
	resource = models.ForeignKey(Resource, related_name='projres')
	project = models.ForeignKey(Project, related_name='projres')
	billing_rate = models.DecimalField(max_digits=8,decimal_places=0)
	title = models.CharField(max_length=40)
	def __str__(self):
		return '{} ({})'.format(self.resource.full_name, self.project.project_name)

class Phase(models.Model):
	project = models.ForeignKey(Project)
	phase_name = models.CharField(max_length=100)
	def __str__(self):
		return '{} --> {}'.format(self.project.name, self.phase_name)
	
class TimeSheet(models.Model):
	created = models.DateTimeField(auto_now=True)
	name = models.CharField(max_length=100)
	resource = models.ForeignKey(Resource)
	
class TimeCard(models.Model):
	created = models.DateTimeField(auto_now=True)
	date_of_work = models.DateField()
	project = models.ForeignKey(Project)
	timesheet = models.ForeignKey(TimeSheet, null=True)
	phase = models.ForeignKey(Phase,null=True,blank=True)
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
			return self.billing_rate() * self.hours
		else:
			return 0.0
	def __str__(self):
		return '{:%Y-%m-%d} {}'.format(self.date_of_work, self.project.project_name)
	
