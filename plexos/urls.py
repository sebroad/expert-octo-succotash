"""plexos URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
import quote.views
import timecards.views
import leaverequest.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
	url(r'^$', quote.views.home),
	url(r'^quote/v1/(?P<quotenum>[0-9a-f\-]{36})', quote.views.quote),
	url(r'^quote/v2/(?P<quotenum>[0-9a-f\-]{36})', quote.views.quote2),
	url(r'^timecards/resource/(?P<resname>[A-Za-z0-9]*)/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})', timecards.views.resourcetime),	
	url(r'^timecards/resource/(?P<resname>[A-Za-z0-9]*)$', timecards.views.resourcetime),	
	url(r'^timecards/resource/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})', timecards.views.resourcetime),	
	url(r'^timecards/resource', timecards.views.resourcetime),	
	url(r'^timecards/project/(?P<projname>[^/]*)/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/{0,1}', timecards.views.projecttime),	
	url(r'^timecards/project/(?P<projname>[^/]*)/{0,1}$', timecards.views.projecttime),	
	url(r'^timecards/project/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})', timecards.views.projecttime),	
	url(r'^timecards/project', timecards.views.projecttime),
	url(r'^timecards/todate/(?P<projid>[0-9]*)/(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})/{0,1}$', timecards.views.todate),	
	url(r'^timecards/todate/(?P<projid>[0-9]*)/{0,1}$', timecards.views.todate),	
	url(r'^timecards/todate/(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})/{0,1}$', timecards.views.todate),	
	url(r'^timecards/todate', timecards.views.todate),	
	url(r'^timecards/billable/(?P<projname>[^/]*)/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/{0,1}', timecards.views.billabletime),	
	url(r'^timecards/billable/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/{0,1}', timecards.views.billabletime),	
	url(r'^timecards/billable/{0,1}$', timecards.views.billabletime),	
	url(r'^timecards/ts/(?P<sheetname>.*)', timecards.views.timesheet),	
	url(r'^timecards/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})$', timecards.views.summary),
	url(r'^timecards/{0,1}$', timecards.views.summary),
	url(r'^leavereq/(?P<requestid>[0-9a-f\-]{36})', leaverequest.views.requestid),
	url(r'^leavereq/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})', leaverequest.views.summary),
	url(r'^leavereq/(?P<year>[0-9]{4})', leaverequest.views.summary),
	url(r'^leavereq/(?P<resource>.*)$', leaverequest.views.resource),
	url(r'^leavereq/{0,1}$', leaverequest.views.summary),
]
