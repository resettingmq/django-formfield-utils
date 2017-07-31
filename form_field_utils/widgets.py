# -*- coding: utf-8 -*-

from django.forms.widgets import Widget


class FormInput(Widget):
    template_name = 'form_field_utils/form_input.html'

    def render(self, name, value, attrs=None, renderer=None, context=None, using_template=None, template_name=None):
        if not using_template:
            return value.as_table()

        template_name = template_name or self.template_name
        context = self.get_context(name, value, attrs, context, template_name)
        return self._render(template_name, context, renderer)

    def value_from_datadict(self, data, files, name):
        return data

    def get_context(self, name, value, attrs, context=None, template_name=None):
        ctx = super().get_context(name, value, attrs)
        ctx['widget']['template_name'] = template_name
        ctx['form'] = value
        context.update(ctx)
        return context
