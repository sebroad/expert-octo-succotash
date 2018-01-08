# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, loader
from django.http import HttpResponse, HttpResponseRedirect
from datetime import date, datetime, timedelta
from django.contrib.auth.decorators import login_required
from .models import *
from django.db.models import Sum, Max, F
from django.db.models.functions import TruncMonth, Substr
from django_pivot.pivot import pivot
import re

# Create your views here.
@login_required
def todate(request, projid = 0, year = '', month = '', day = ''):
	if year == '':
		to = datetime.today()
	elif month == '':
		to = datetime(int(year), 1, 1)
	elif day == '':
		to = datetime(int(year), int(month), 1)
	else:
		to = datetime(int(year), int(month), int(day))
	projects = Project.objects.all()
	cards = TimeCard.objects.filter(project__id=projid, date_of_work__lte=to)
	results, hours, cost = todatesummary(cards, projid)
	budget = float(projects.filter(id=projid).aggregate(Max('budget'))['budget__max'])
	c = dict(results=results, projects=projects, hours=hours, cost=cost, \
			 budget=budget, remaining=budget-cost, asof='{:%Y-%m-%d}'.format(to))
	t = loader.get_template("todate.html")
	return HttpResponse(t.render(c))

def todatesummary(cards, projid):
	
	# query
	results = cards.annotate( \
			month=TruncMonth('date_of_work'), \
			name=Substr('timesheet__resource__full_name', 1), \
			proj=Substr('project__project_name', 1)) \
		.values('name', 'proj', 'month') \
		.annotate(total_hours=Sum('hours')).order_by('month','name')
	
	rates = pivot(ProjectResource.objects.filter(project__id=projid),'project__id','resource__full_name','billing_rate')
	
	total_hours = 0.0
	total_cost = 0.0
	
	for row in results:
		rate = float(rates[0][row['name']]) if len(rates) > 0 and row['name'] in rates[0] else 0.0
		row['cost'] = rate * float(row['total_hours'])
		total_hours += float(row['total_hours'])
		total_cost += row['cost']
		
	return results, total_hours, total_cost

@login_required
def timesheet(request, sheetname):
	cards = TimeCard.objects.filter(timesheet__name=sheetname).order_by('date_of_work', 'project__project_name')
	c = dict({'timecards': cards, 'title': sheetname})
	t = loader.get_template("user.html")
	return HttpResponse(t.render(c))	

@login_required
def resourcetime(request, resname='', year=None, month=None):
	if year == None or month == None:
		url = '{}/{}/{:02d}'.format(request.path, datetime.today().year, datetime.today().month)
		return HttpResponseRedirect(url.replace('//','/'))

	dt = date(int(year), int(month), 1)
	nx = dt + timedelta(31)
	pv = dt - timedelta(1)
	next = re.sub('/[0-9]{4}/[0-9]{2}', '/{}/{:02d}'.format(nx.year, nx.month), request.path)
	prev = re.sub('/[0-9]{4}/[0-9]{2}', '/{}/{:02d}'.format(pv.year, pv.month), request.path)

	cards = TimeCard.objects.filter(timesheet__resource__username__username__icontains=resname, \
									date_of_work__year=year, date_of_work__month=month)
	cards = cards.order_by('timesheet__resource__username__last_name', 'date_of_work')
	title = '{} ({}-{})'.format('Resources' if resname == '' else resname, year, month)
	c = dict({'timecards': cards, 'title': title, 'next': next, 'prev': prev})
	t = loader.get_template("user.html")
	return HttpResponse(t.render(c))

@login_required
def projecttime(request, projname='', year=None, month=None):
	if year == None or month == None:
		url = '{}/{}/{:02d}'.format(request.path, datetime.today().year, datetime.today().month)
		return HttpResponseRedirect(url.replace('//','/'))
	
	dt = date(int(year), int(month), 1)
	nx = dt + timedelta(31)
	pv = dt - timedelta(1)
	next = re.sub('/[0-9]{4}/[0-9]{2}', '/{}/{:02d}'.format(nx.year, nx.month), request.path)
	prev = re.sub('/[0-9]{4}/[0-9]{2}', '/{}/{:02d}'.format(pv.year, pv.month), request.path)

	cards = TimeCard.objects.filter(project__project_name__icontains=projname, date_of_work__year=year, date_of_work__month=month)
	cards = cards.order_by('project__project_name', 'date_of_work')
	c = dict({'timecards': cards, 'title': '{} ({}-{})'.format('All projects' if len(projname) == 0 else projname, year, month), 'next': next, 'prev': prev})
	t = loader.get_template("project.html")
	return HttpResponse(t.render(c))	
	
@login_required
def billabletime(request, projname='', year=None, month=None):
	if year == None or month == None:
		url = '{}/{}/{:02d}'.format(request.path, datetime.today().year, datetime.today().month)
		return HttpResponseRedirect(url.replace('//','/'))

	dt = date(int(year), int(month), 1)
	nx = dt + timedelta(31)
	pv = dt - timedelta(1)
	next = re.sub('/[0-9]{4}/[0-9]{2}', '/{}/{:02d}'.format(nx.year, nx.month), request.path)
	prev = re.sub('/[0-9]{4}/[0-9]{2}', '/{}/{:02d}'.format(pv.year, pv.month), request.path)

	cards = TimeCard.objects.filter( \
			project__project_name__icontains=projname, \
			project__billing_method__is_billed=True, \
			date_of_work__year=year, \
			date_of_work__month=month)
	
	c = dict()
	c['timecards'] = consulting(cards)
	c['title'] = 'Consulting ({}-{})'.format(year, month)
	c['next'] = next
	c['prev'] = prev
	c['year'] = year
	c['month'] = month
	t = loader.get_template("consulting.html")
	return HttpResponse(t.render(c))	

def consulting(cards):
	results = []
	for proj in cards.values('project__project_name').distinct():
		projcards=cards.filter(project__project_name=proj['project__project_name'])
		results2 = []
		for res in projcards.values('timesheet__resource__full_name').distinct():
			rescards = projcards.filter(timesheet__resource__full_name=res['timesheet__resource__full_name'])
			rescards = rescards.order_by('date_of_work','phase__phase_name')
			results2.append(dict(resource_name=res['timesheet__resource__full_name'], total=sum([c.total() for c in rescards]), cards=rescards))
		results.append(dict(project_name=proj['project__project_name'], total=sum([c.total() for c in projcards]), resource_detail=results2))
		
	return results

	
@login_required
def summary(request, year=None, month=None):
	if year == None or month == None:
		url = '{}/{}/{:02d}'.format(request.path, datetime.today().year, datetime.today().month)
		return HttpResponseRedirect(url.replace('//','/'))
	cards = TimeCard.objects.filter(date_of_work__year=year, date_of_work__month=month)
	
	dt = date(int(year), int(month), 1)
	nx = dt + timedelta(31)
	pv = dt - timedelta(1)
	next = re.sub('/[0-9]{4}/[0-9]{2}', '/{}/{:02d}'.format(nx.year, nx.month), request.path)
	prev = re.sub('/[0-9]{4}/[0-9]{2}', '/{}/{:02d}'.format(pv.year, pv.month), request.path)

	c = dict()
	c['resources'] = cards.values('timesheet__resource__full_name') \
				.annotate(Sum('hours')) \
				.order_by('timesheet__resource__full_name')
	c['projects'] = cards.values('project__project_name') \
				.annotate(Sum('hours')) \
				.order_by('project__project_name')
	c['daily'] = pivot(cards.order_by('date_of_work'),'date_of_work','project__project_group__name','hours')
	c['year'] = year
	c['month'] = month
	c['next'] = next
	c['prev'] = prev
	c['title'] = 'Resource Utilization Summary -- {}-{}'.format(year, month)
	t = loader.get_template("month.html")
	return HttpResponse(t.render(c))

def summarize_projects(cards):
	res = dict()
	
	for card in cards:
		proj = card.project.project_name
		if proj not in res:
			res[proj] = 0.0
		res[proj] += float(card.hours)
	
	data = [{'name': k, 'hours': res[k]} for k in sorted(res.keys())]
	return data
