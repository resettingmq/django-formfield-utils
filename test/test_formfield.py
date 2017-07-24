# -*- coding: utf-8 -*-

import copy

from django.test import TestCase
from django.forms.fields import BoundField
from django.core.exceptions import ImproperlyConfigured

from form_field_utils.fields import FormField
from .forms import OuterForm, InnerForm


class FormFieldTestCase(TestCase):
    outer_form_data = {
        'other_field_0': 'val0',
        'other_field_1': 'val1',
        'form_field-inner_field': 'inner_val0',
        'form_field-inner_field_with_outer_form_initial': 'inner_val1'
    }

    def setUp(self):
        self.inner_form = InnerForm()
        self.outer_form = OuterForm()

    def test_form_can_render(self):
        try:
            self.outer_form.as_p()
        except:
            self.fail('FormField caused Form render failed')

    def test_can_render_title(self):
        pass

    def test_improper_form_class_module_path_raise_exception(self):
        form_field = FormField('not_exsited_module')
        with self.assertRaises(ImproperlyConfigured):
            form_field.get_form()

    def test_improper_form_class_raise_exception(self):
        form_field = FormField(str)
        with self.assertRaises(ImproperlyConfigured):
            form_field.get_form()

    def test_can_passed_in_Form_class_and_render_it(self):
        self.assertIn('inner_field', str(self.outer_form))

    def test_form_field_can_access_subfield_by_fields_name(self):
        form_field = self.outer_form['form_field']
        for name in self.inner_form.fields:
            self.assertEqual(self.inner_form[name].name, form_field[name].name)

    def test_form_field_is_iterable(self):
        try:
            for sub_field in self.outer_form['form_field']:
                self.assertTrue(isinstance(sub_field, BoundField))
        except TypeError:
            self.fail('FormField is not iterable')

    def test_form_field_name_prefix_render_properly(self):
        form_field = self.outer_form['form_field']
        html = str(form_field)
        self.assertIn('name="form_field-inner_field"', html)

    def test_form_field_initial_properly_set(self):
        outer_form = OuterForm(
            initial={
                'form_field': {
                    'inner_field_with_outer_form_initial': 'outer form initial'
                }
            }
        )
        html = outer_form.as_p()
        self.assertIn('outer form initial', html)
        self.assertIn('inner form initial', html)
        self.assertIn('inner form field initial', html)

    def test_form_field_can_render_data_kwarg(self):
        outer_form = OuterForm(self.outer_form_data)
        html = outer_form.as_p()
        self.assertInHTML(
            '''<input type="text" name="form_field-inner_field_with_outer_form_initial"
            id="id_form_field-inner_field_with_outer_form_initial" required
            value="inner_val1" />''',
            html
        )
        self.assertInHTML(
            '''<input type="text" name="form_field-inner_field" id="id_form_field-inner_field" required
            value="inner_val0" />''',
            html
        )

    def test_form_field_get_data_properly(self):
        expected = {
            'inner_field': 'inner_val0',
            'inner_field_with_initial': None,
            'inner_field_with_inner_form_initial': None,
            'inner_field_with_outer_form_initial': 'inner_val1',
        }
        outer_form = OuterForm(self.outer_form_data)
        self.assertEqual(expected, outer_form['form_field'].data)

    def test_form_field_validation(self):
        outer_form = OuterForm(self.outer_form_data)
        outer_form.full_clean()
        form_field_errors = outer_form.errors['form_field']
        self.assertEqual(len(form_field_errors), 1)
        self.assertIn(
            'Field inner_field_with_inner_form_initial in FormField',
            form_field_errors[0]
        )

    def test_form_field_get_cleaned_data_properly(self):
        expected = {
            'inner_field': 'inner_val0',
            'inner_field_with_initial': 'inner_val2',
            'inner_field_with_inner_form_initial': 'inner_val3',
            'inner_field_with_outer_form_initial': 'inner_val1',
        }
        outer_form_data = copy.copy(self.outer_form_data)
        outer_form_data.update({
            'form_field-inner_field_with_initial':'inner_val2',
            'form_field-inner_field_with_inner_form_initial': 'inner_val3',

        })
        outer_form = OuterForm(outer_form_data)
        outer_form.full_clean()

        self.assertEqual(
            outer_form.cleaned_data['form_field'],
            expected
        )

    def test_form_field_required_false_no_render(self):
        self.outer_form.fields['form_field'].required = False
        form_field = self.outer_form['form_field']
        html = str(form_field)
        self.assertNotIn('required', html)

    def test_form_field_required_false_no_validation_error(self):
        outer_form = OuterForm(self.outer_form_data)
        outer_form.fields['form_field'].required = False
        self.assertEqual(len(outer_form.errors), 0)

    def test_form_field_disabled_true_render(self):
        self.outer_form.fields['form_field'].disabled = True
        form_field = self.outer_form['form_field']
        html = str(form_field)
        self.assertInHTML(
            """<input type="text" name="form_field-inner_field"
            id="id_form_field-inner_field" disabled required />""",
            html
        )
        self.assertInHTML(
            """<input type="text" name="form_field-inner_field_with_initial"
            value="inner form field initial" id="id_form_field-inner_field_with_initial" disabled />""",
            html
        )
        self.assertInHTML(
            """<input type="text" name="form_field-inner_field_with_inner_form_initial"
            value="inner form initial" id="id_form_field-inner_field_with_inner_form_initial"
            required disabled />""",
            html
        )
        self.assertInHTML(
            """<input type="text" name="form_field-inner_field_with_outer_form_initial"
            id="id_form_field-inner_field_with_outer_form_initial" required disabled />""",
            html
        )
