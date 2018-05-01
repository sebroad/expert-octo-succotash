# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, loader
from django.http import HttpResponse, HttpResponseRedirect

from .models import *

# Create your views here.
def requestid(request, requestid):
	leavereq = LeaveRequest.objects.filter(id=requestid)
	
	if len(leavereq) == 0:
		c = dict({'title': 'Request not found'})
	else:
		c = dict({'request': leavereq[0], 'title': 'Leave Request for ' + leavereq[0].name.username.first_name})

	t = loader.get_template("leaverequest.html")
	return HttpResponse(t.render(c))	
	
def summary(request, year, month):
	pass