from django.template.defaulttags import register
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """ custom filter to access dict by key in templates """
    return dictionary.get(key)
