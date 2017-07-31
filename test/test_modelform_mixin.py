# -*- coding: utf-8 -*-


from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured
from django import forms as django_forms

from form_field_utils.forms import ModelFormFieldSupportMixin
from form_field_utils.fields import ModelFormField
from . import forms
from .models import Case, Application


class ModelFormMixinTestCase(TestCase):

    def setUp(self):
        self.case = Case.objects.create(name='Test case 1')
        self.application = Application.objects.create(no='x0001', case=self.case)

    def test_model(self):
        self.assertEqual(self.case.application.no, self.application.no)

    def test_can_only_collection_modelform_field_for_one_to_one_rel_field(self):
        test_form = forms.TestCaseModelForm()
        self.assertEqual(test_form.modelform_fields, {})

        case_form = forms.CaseModelForm()
        self.assertEqual(len(case_form.modelform_fields), 1)
        self.assertIsNotNone(case_form.modelform_fields.get('application'))

    def test_outer_modelform_instance_value_can_pass_to_modelformfield(self):
        case_form = forms.CaseModelForm(instance=self.case)
        inner_form = case_form['application'].inner_form
        self.assertTrue(isinstance(inner_form.instance, Application))
        self.assertEqual(inner_form.instance.id, self.case.application.id)

    def test_modelformfield_model_match(self):

        class ErrorCaseModelForm(ModelFormFieldSupportMixin, django_forms.ModelForm):
            application = ModelFormField(forms.TestModelForm)

            class Meta:
                model = Case
                fields = '__all__'

        with self.assertRaises(ImproperlyConfigured):
            form = ErrorCaseModelForm()

    def test_inner_form_related_to_out_model_field_auto_deleted(self):
        case_form = forms.CaseModelForm()
        html = case_form.as_p()
        self.assertNotIn('Case:', html)

    def test_save_commit(self):
        outerform_data = {
            'name': 'Test case 2',
            'no': 'x0002'
        }
        case_form = forms.CaseModelForm(outerform_data)
        case_form.save()
        case = Case.objects.filter(name='Test case 2').get()
        self.assertEqual(case.name, 'Test case 2')
        self.assertEqual(case.application.no, 'x0002')
        app = Application.objects.filter(no='x0002').get()
        self.assertEqual(app.case.name, 'Test case 2')

    def test_save_no_commit(self):
        outerform_data = {
            'name': 'Test case 2',
            'no': 'x0002'
        }
        case_form = forms.CaseModelForm(outerform_data)
        case = case_form.save(commit=False)
        self.assertEqual(case.name, 'Test case 2')
        self.assertEqual(case.application.no, 'x0002')
        with self.assertRaises(Case.DoesNotExist):
            case = Case.objects.filter(name='Test case 2').get()
        with self.assertRaises(Application.DoesNotExist):
            app = Application.objects.filter(no='x0002').get()
