# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, loader
from django.http import HttpResponse, HttpResponseRedirect

from .models import *

# Create your views here.
def requestid(request, requestid):
	leavereq = LeaveRequest.objects.filter(id=requestid)
	approval = LeaveApproval.objects.filter(request__id=requestid).order_by('-approval_timestamp')
	
	if len(leavereq) == 0:
		c = dict({'title': 'Request not found'})
	elif len(approval) == 0:
		c = dict({'request': leavereq[0]})
	else:
		c = dict({'request': leavereq[0], 'approval': approval[0]})

	t = loader.get_template("leaverequest.html")
	return HttpResponse(t.render(c))	
	
def summary(request, year = None, month = None):
	if year is None:
		url = '{}/{}/'.format(request.path, datetime.today().year)
		return HttpResponseRedirect(url.replace('//','/'))
	if month is None:
		'''
		Create an annual report for current year
		Pivot requested and approved leaves by month, resource
		'''
		reqs = LeaveDay.objects.filter(date_of_leave__year=int(year))
		return HttpResponse(reqs)
		
	else:
		'''
		Create a monthly report for selected month
		Pivot requested and approved leaves by day, resource
		'''
		reqs = LeaveDay.objects.filter(date_of_leave__year=int(year), date_of_leave__month=int(month))
		return HttpResponse(reqs)
		
	pass