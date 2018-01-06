from django import forms
from .models import Recipient

class EmailSearchForm(forms.ModelForm):
	class Meta:
		model = Recipient
		fields = ['email',]
		
class RecipientForm(forms.ModelForm):
	class Meta:
		model = Recipient
		fields = ['fname','lname','company','email',]
		labels = {'fname': 'First Name', 'lname': 'Last Name'}