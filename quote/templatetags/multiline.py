from django import template

register = template.Library()

@register.filter
def multiline(value):
	return value.replace('\n','<br/>')