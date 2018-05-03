# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Max, F
from django.db.models.functions import TruncMonth, TruncDay, Substr
from django_pivot.pivot import pivot

from .models import *

# Create your views here.

@login_required
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
	

@login_required
def summary(request, year = None, month = None):
	if year is None:
		url = '{}/{}/'.format(request.path, datetime.today().year)
		return HttpResponseRedirect(url.replace('//','/'))
		
	c = dict(year=year,month=month)
	
	if month is None:
		'''
		Create an annual report for current year
		Pivot requested and approved leaves by month, resource
		'''
		reqs = LeaveDay.objects.filter(date_of_leave__year=int(year)).annotate(month=TruncMonth('date_of_leave'))							
		pivot_tbl = pivot(reqs, 'month', 'request__name__username__username', 'hours').order_by('month')
		
		t = loader.get_template('monthly.html')
		
	else:
		'''
		Create a monthly report for selected month
		Pivot requested and approved leaves by day, resource
		'''
		reqs = LeaveDay.objects.filter(date_of_leave__year=int(year), date_of_leave__month=int(month)).annotate(day=TruncDay('date_of_leave'))
		pivot_tbl = pivot(reqs, 'day', 'request__name__username__username', 'hours').order_by('day')
		
		t = loader.get_template('daily.html')
		c['prev'] = datetime(int(year),int(month),1)-timedelta(1)
		c['next'] = datetime(int(year),int(month),1)+timedelta(31)
		
	c['pivot_tbl'] = pivot_tbl
	
	return HttpResponse(t.render(c))

	
@login_required
def resource(request, resource=''):
	start = datetime.today() - timedelta(182)
	end = start + timedelta(365)
	
	leavedays = LeaveDay.objects.filter(request__name__username__username__startswith=resource, \
										date_of_leave__gte=start, date_of_leave__lt=end) \
										.annotate(Month=TruncMonth('date_of_leave'))
	pivot_tbl = pivot(leavedays, 'Month', 'request__leave_type', 'hours').order_by('Month')
	c = dict({'title': 'Report for ' + resource,'leavedays': leavedays, \
			  'resource':resource,'start':start,'end':end,'pivot_tbl': pivot_tbl})
	t = loader.get_template("resource.html")
	return HttpResponse(t.render(c))	
