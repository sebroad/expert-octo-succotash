# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.shortcuts import render, loader
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import *
import re

# Create your views here.
def home(request):
	if request.method == "GET":
		sections = Section.objects.all()
		t = loader.get_template('home.html')
		form = EmailSearchForm()
		c = dict({'sections': sections, 'form': form})
		return HttpResponse(t.render(c,request=request))
	elif request.method == "POST":
		if 'company' in request.POST:
			return HttpResponse('Hello World!')
		else:
			sections = Section.objects.all()
			recipients = Recipient.objects.filter(email__iexact=request.POST['email'])
			quotes = Quote.objects.filter(recipient__email__iexact=request.POST['email'])
			
			data = dict({'email': request.POST['email']})
			
			if len(recipients) == 0:
				message = "We couldn't find your info. Here's our best guess."
				m = re.match('(?P<fname>[a-z0-9]*)[^@]{0,1}(?P<lname>[^@]*)@(.*)', request.POST['email'].lower())
				data['fname'] = m.group(1).title()
				data['lname'] = m.group(2).title()
				data['company'] = m.group(3).replace('.',' ').title()
			else:
				message = "Welcome back! We found your info. You can update it if you like."
				data['fname'] = recipients[0].fname
				data['lname'] = recipients[0].lname
				data['company'] = recipients[0].company
			
			form = RecipientForm(data)

			t = loader.get_template('home.html')
			c = dict({'sections': sections, 'form': form, 'message': message, 'quotes': quotes})
			return HttpResponse(t.render(c,request=request))
	
@login_required
def quote(request, quotenum):
	quote = Quote.objects.filter(id=quotenum)
	items = LineItem.objects.filter(quote__id=quotenum).order_by('product__section__order', 'product__order_in_section')
	totals = get_totals(items)
	c = dict({'quote': quote, 'items': items, \
			  'totals': totals, \
			  'preamble': get_preamble(quote[0],totals), \
			  'signature': quote[0].signature,\
			  })
	t = loader.get_template('quote.html')
	return HttpResponse(t.render(c))

def get_preamble(quote, totals):
	x = ''

	# Software?
	if totals['software'] > 0.1:

		# Intro
		x += "Please find below your quote for PLEXOS Licensing. "
		x += "This quote includes "

		if totals['weeks'] > 0 and totals['engine'] > 0:
			x += str(totals['weeks']) + " weeks of PLEXOS licensing"
		elif totals['engine'] > 0:
			x += str(totals['engine']) + " PLEXOS license(s)"
		if totals['solver'] > 0:
			x += ' and {} solver (or solver support) license(s). '.format(totals['solver'])
		else:
			x += ". "

		x += '\n\n'
		if totals['already'] > 0:
			x += ' This quote is an incremental quote. Licensing under the current contract is '
			x += 'indicated as "Paid" in the line item description. Totals are additional to existing licensing. '
		
		if quote.future_year > 0:
			x += ' This quote is for future year pricing {} year(s) beyond the present pricing year. '.format(quote.future_year)

		x += '\n\n'
		if totals['gas'] + totals['water'] > 0:
			x += ' As requested, your quote includes '
			if totals['gas'] > 0 and totals['water'] > 0:
				x += '{} PLEXOS Gas licenses and {} PLEXOS Water licenses. '.format(totals['gas'], totals['water'])
			elif totals['gas'] > 0:
				x += '{} PLEXOS Gas licenses. '.format(totals['gas'])
			else:
				x += '{} PLEXOS Water licenses. '.format(totals['gas'], totals['water'])

		x += ' Our representatives are happy to introduce the PLEXOS Integrated '
		x += 'Energy model modules (Electric, Gas, Water) if you need further information. '
		
		if totals['connect'] > 0:
			x += "The PLEXOS Connect server is also included in this quote. "
		else:
			x += 'PLEXOS Connect Server -- providing license server, execution management, '
			x += 'and data management -- is not included in this quote. Ask our representatives '
			x += 'for more information about this product. '

		if totals['usb'] > 0:
			x += "This quote includes {} USB Function licenses for license portability. ".format(totals['usb'])
		elif totals['connect'] == 0:
			x += "Please ask about USB Function licenses for license portability if this is desired. "
		
	else: #services only
		x += "Please find your quote below for PLEXOS services. "
		x += "Should you have a need for PLEXOS software licensing, "
		x += "please contact us via the contact information below. "

	if totals['training'] > 0:
		if totals['onsitetraining'] > 0:
			x += '\n\nA quote for on-site PLEXOS training is included. Training '
			x += 'sessions admit at most ten trainees from your company. This '
			x += 'quote provides estimates for travel expenses. PLEXOS training '
			x += 'is also offered at our regional offices at intervals. This option '
			x += 'is often less expensive for small groups of trainees. Please '
			x += 'inquire if interested. '
		else:
			x += '\n\nA quote for PLEXOS training is included. This quote does not '
			x += 'include your travel costs to attend the training which will be '
			x += 'scehduled at a date and location determined by Energy Exemplar '
			x += '(typically several times a year at our offices). Energy Exemplar '
			x += 'can also provide customized training at your site. Please inquire '
			x += 'if interested. '
	if totals['impl'] > 0:
		x += "\n\nA quote for PLEXOS implementation services is shown below. PLEXOS Implementation services are illustrative only. Implementation services require further agreement on the Scope of Work. "
		
	if totals['discount'] > 0:
		x += "\n\nThe quote identifies one or more areas of savings that have been applied to your pricing request. "

	if quote.num_years > 1: 
		x+= "\n\nThis quote provides licensing for a period of {} years from the commencement of the license agreement.".format(quote.num_years)

	return x
	
def get_totals(items):	
	totals = dict()
	totals['software'] = 0
	totals['softdisc'] = 0
	totals['softsub'] = 0
	totals['subtotal'] = 0
	totals['discount'] = 0
	totals['total'] = 0
	totals['impl'] = 0
	totals['impldisc'] = 0
	totals['implsub'] = 0
	totals['data'] = 0
	totals['datasub'] = 0
	totals['datadisc'] = 0
	totals['weeks'] = 0
	totals['engine'] = 0
	totals['solver'] = 0
	totals['electric'] = 0
	totals['gas'] = 0
	totals['water'] = 0
	totals['already'] = 0
	totals['connect'] = 0
	totals['usb'] = 0
	totals['training'] = 0
	totals['onsitetraining'] = 0
	for item in items.filter(quote__num_years__gt=1):
		for year in item.quote.get_multi_year_range(): 
			totals['totals_' + str(year) ] = 0
			if item.product.is_software: 
				totals['software_'+ str(year)] = 0
			if item.product.is_data: 
				totals['datasub_'+ str(year)] = 0
			if item.product.is_implementation: 
				totals['impl_'+ str(year)] = 0
			if item.product.is_training: 
				totals['training_'+ str(year)] = 0


	for item in items:
		totals['total'] += item.total()
		totals['subtotal'] += item.subtotal()
		totals['discount'] += item.discount()
		totals['training'] += item.total() if item.product.is_training else 0
		totals['onsitetraining'] += item.total() if item.product.is_training and item.product.is_onsite else 0

	for item in items.filter(product__is_software=True):
		totals['software'] += item.total()
		totals['softsub'] += item.subtotal()
		totals['softdisc'] += item.discount()
		totals['already'] += item.already
		totals['connect'] += 1 if 'connect' in item.product.name.lower() else 0
		totals['engine'] += item.quantity if item.product.is_engine else 0
		totals['electric'] += item.quantity if item.product.is_electric else 0
		totals['gas'] += item.quantity if item.product.is_gas else 0
		totals['water'] += item.quantity if item.product.is_water else 0
		totals['solver'] += item.quantity if item.product.is_solver else 0
		if item.termincr.text.lower() == 'week':
			totals['weeks'] = max(totals['weeks'],item.numterms)
		
	for item in items.filter(product__is_implementation=True):
		totals['impl'] += item.total()
		totals['impldisc'] += item.discount()
		totals['implsub'] += item.subtotal()

	for item in items.filter(product__is_data=True):
		totals['data'] += item.total()
		totals['datasub'] += item.subtotal()
		totals['datadisc'] += item.discount()
		
	for item in items.filter(quote__num_years__gt=1):
		for year, year_subtotal in item.get_multi_year_subtotal().iteritems(): 
			totals['totals_' + str(year) ] += year_subtotal
			if item.product.is_software: 
				totals['software_'+ str(year)] += year_subtotal
			if item.product.is_data:  
				totals['datasub_'+ str(year)] += year_subtotal
			if item.product.is_implementation: 
				totals['impl_'+ str(year)] += year_subtotal
			if item.product.is_training: 
				totals['training_'+ str(year)] += year_subtotal


	return totals
