# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from timecards.models import Resource
from datetime import datetime, timedelta
from django import forms
import django.utils.timezone
import uuid

# Create your models here.
class LeaveRequest(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
	LEAVE_TYPE = [('PTO', 'Vacation/PTO'),('FLT', 'Floating Holiday'),('SIC','Sick'),]
	name = models.ForeignKey(Resource)
	amended = models.BooleanField(default=False)
	
	leave_type = models.CharField(max_length=3, choices=LEAVE_TYPE, default='PTO')
	application_date = models.DateTimeField(auto_now=True)
	
	def get_num_leave_days(self):
		return sum([1 if day.hours == 8 else 0 for day in LeaveDay.objects.filter(request__id=self.id)])
		
	def get_num_leave_hours(self):
		return sum([0 if day.hours == 8 else day.hours for day in LeaveDay.objects.filter(request__id=self.id)])
		
	def get_first_leave_day(self):
		return min([day.date_of_leave for day in LeaveDay.objects.filter(request__id=self.id)])
		
	def get_last_leave_day(self):
		return max([day.date_of_leave for day in LeaveDay.objects.filter(request__id=self.id)])
		
	def get_leave_schedule_table(self):
		mylist = []
		days = [(day.date_of_leave, day.note) for day in LeaveDay.objects.filter(request__id=self.id).order_by('date_of_leave')]
		week = []
		while len(days) > 0:
			if len(week) == 0:
				first_date_of_week = days[0][0] - timedelta(days=days[0][0].weekday())
				week = [first_date_of_week + timedelta(days=i) for i in range(7)]
			cell_date = week.pop(0)
			if cell_date == days[0][0]:
				day = days.pop(0)
				mylist.append(day)
			else:
				mylist.append((None,None))
		
		mylist += [(None,None)]*len(week)
			
		#print mylist
		return mylist
		
	def is_approved(self):
		return len(LeaveApproval.objects.filter(request__id=self.id, approval_timestamp__gte=self.application_date)) > 0
		
	def __str__(self):
		return '{} ({:%m/%d/%y}-{:%m/%d/%y})'.format(self.name.get_full_name(), self.get_first_leave_day(), self.get_last_leave_day())
		
	
	
class LeaveDay(models.Model):
	date_of_leave = models.DateField()
	hours = models.PositiveSmallIntegerField(default=8)
	note = models.CharField(max_length=280, blank=True)
	request = models.ForeignKey('LeaveRequest',on_delete=models.CASCADE)
	def __str__(self):
		return '{:%m/%d/%y} {} --> {}'.format(self.date_of_leave, self.request.name, self.hours)
	
class LeaveApproval(models.Model):
	approver = models.ForeignKey(Resource)
	approval_timestamp = models.DateTimeField(auto_now=True)
	request = models.ForeignKey('LeaveRequest',on_delete=models.CASCADE)
	def __str__(self):
		return str(self.request)
	
