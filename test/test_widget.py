# -*- coding: utf-8 -*-

from django.test import TestCase

from form_field_utils.widgets import FormInput

from .forms import InnerForm


class WidgetTestCase(TestCase):
    def test_can_render(self):
        widget = FormInput()
        inner_form = InnerForm()
        html = widget.render('field_name', inner_form)
        for field in inner_form:
            self.assertIn(str(field), html)
