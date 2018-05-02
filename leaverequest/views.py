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
	
def summary(request, year, month):
	pass