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
def summary_test(request, year=None, month=None):
	if year == None or month == None:
		url = '{}/{}/{:02d}'.format(request.path, datetime.today().year, datetime.today().month)
		return HttpResponseRedirect(url.replace('//','/'))
	
	dt = date(int(year), int(month), 1)
	nx = dt + timedelta(31)
	pv = dt - timedelta(1)
	next = re.sub('/[0-9]{4}/[0-9]{2}', '/{}/{:02d}'.format(nx.year, nx.month), request.path)
	prev = re.sub('/[0-9]{4}/[0-9]{2}', '/{}/{:02d}'.format(pv.year, pv.month), request.path)

	cards = TimeCard.objects.filter(project__project_name__icontains=projname, \
		date_of_work__year=year, date_of_work__month=month)
	
	pivot_tbl = pivot(cards, 'date_of_work', 'project__project_name', 'hours').order_by('date_of_work')
	cards = cards.order_by('project__project_name', 'date_of_work')
	if projname == '':
		c = dict({'pivot': pivot_tbl, 'year': year, 'month': month, \
			'title': 'All projects ({}-{})'.format(year, month), \
			'next': next, 'prev': prev})
	else:
		c = dict({'timecards': cards, 'year': year, 'month': month, \
			'title': '{} ({}-{})'.format(projname, year, month), \
			'next': next, 'prev': prev})
		
	t = loader.get_template("project.html")
	return HttpResponse(t.render(c))	

@login_required
def summary(request, year = None, month = None):
	if year is None:
		url = '{}/{}/'.format(request.path, datetime.today().year)
		return HttpResponseRedirect(url.replace('//','/'))
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
		
	c = dict(pivot_tbl=pivot_tbl,year=year,month=month)
	
	return HttpResponse(t.render(c))
pass

@login_required
def resource(request, resource=''):
	pass
