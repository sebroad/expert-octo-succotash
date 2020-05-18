from django.shortcuts import render, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Max, F
from django.db.models.functions import TruncMonth, TruncDay, Substr
from django_pivot.pivot import pivot

from .models import *

@login_required
def summary(request, planid):
    c = dict(plans=ImplementationPlan.objects.filter(id = planid))
    t = loader.get_template("summary.html")
    return HttpResponse(t.render(c))	

@login_required
def gantt(request, planid):
    c = dict(plans=ImplementationPlan.objects.filter(id = planid))
    t = loader.get_template("gantt.csv")
    return HttpResponse(t.render(c), content_type='text/plain')
