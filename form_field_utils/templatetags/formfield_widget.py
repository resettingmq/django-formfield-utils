# -*- coding: utf-8 -*-

"""
实现formfield相关的filter
"""

from django.template import Library
from ..fields import BaseFormField

register = Library()


@register.filter
def is_formfield(field):
    return isinstance(field.field, BaseFormField)
