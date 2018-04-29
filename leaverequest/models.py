# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
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
	name = models.OneToOneField(User)
	amended = models.BooleanField(default=False)
	leave_type = models.CharField(max_length=3, choices=[('PTO', 'Vacation/PTO'),('FLT', 'Floating Holiday'),('SIC','Sick'),], default='PTO')
	application_date = models.DateTimeField(auto_now=True)
	
class LeaveDay(models.Model):
	date_of_leave = models.DateField()
	hours = models.PositiveSmallIntegerField(default=8)
	note = models.CharField(max_length=280)
	request = models.ForeignKey('LeaveRequest',on_delete=models.CASCADE)
	
class LeaveApproval(models.Model):
	approver = models.OneToOneField(User)
	approval_timestamp = models.DateTimeField(auto_now=True)
	
