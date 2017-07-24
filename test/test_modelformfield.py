# -*- coding: utf-8 -*-

from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured

from form_field_utils.fields import ModelFormField

from .models import TestModel
from . import forms


class ModelFormFieldTestCase(TestCase):
    outer_form_data = {
        'other_field': 'val0',
        'field_0': 'inner_val0',
        # 'field_1': 'inner_val1',
    }

    def setUp(self):
        self.instance = TestModel(field_0='field_0', field_1='field_1')

    def test_improper_form_class_import_path_raise_exception(self):
        form_field = ModelFormField('not existed path')
        with self.assertRaises(ImproperlyConfigured):
            form_field.get_form()

    def test_improper_form_class_raise_exception(self):
        form_field = ModelFormField(str)
        with self.assertRaises(ImproperlyConfigured):
            form_field.get_form()

    def test_improper_model_class_raise_exception(self):
        form_field = ModelFormField(model=str)
        with self.assertRaises(ImproperlyConfigured):
            form_field.get_form()

    def test_fields_not_set_raise_exception(self):
        form_field = ModelFormField(model=TestModel)
        with self.assertRaises(ImproperlyConfigured):
            form_field.get_form()

    def test_fields_can_proper_rendered(self):
        outer_form = forms.ModelOuterFormWithModelFields()
        self.assertIn('field_0', outer_form.as_p())

    def test_instance_argument_can_be_render(self):
        outer_form = forms.ModelOuterFormWithModelForm()
        outer_form.fields['form_field'].instance = self.instance
        html = outer_form.as_p()
        self.assertIn('value="field_0"', html)
        self.assertIn('value="field_1"', html)

    def test_can_retrieve_object(self):
        outer_form = forms.ModelOuterFormWithModelForm(self.outer_form_data)
        outer_form.fields['form_field'].instance = self.instance
        print(self.instance.field_1)
        outer_form.full_clean()

        obj = outer_form['form_field'].save()
        print(outer_form['form_field'].inner_form.cleaned_data)
        self.assertEqual(obj.field_0, 'inner_val0')
        self.assertEqual(obj.field_1, '')
