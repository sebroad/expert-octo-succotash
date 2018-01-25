from django import template

register = template.Library()

@register.filter
def keyvalue(dict, key):    
    try:
        return '' if dict[key] == None else dict[key]
    except KeyError:
        return ''