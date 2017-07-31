# -*- coding: utf-8 -*-

from django import forms

from form_field_utils.fields import FormField, ModelFormField
from form_field_utils.forms import FormFieldSupportMixin, ModelFormFieldSupportMixin

from .models import TestModel, Case, Application


class InnerForm(forms.Form):
    inner_field = forms.CharField()
    inner_field_with_initial = forms.CharField(initial='inner form field initial', required=False)
    inner_field_with_inner_form_initial = forms.CharField()
    inner_field_with_outer_form_initial = forms.CharField()


class OuterForm(FormFieldSupportMixin, forms.Form):
    form_field = FormField(
        InnerForm,
        initial={'inner_field_with_inner_form_initial': 'inner form initial'},
        prefix='form_field'
    )
    other_field_0 = forms.CharField()
    other_field_1 = forms.CharField()


class ModelInnerForm(forms.ModelForm):
    class Meta:
        model = TestModel
        fields = ['field_0', 'field_1']


class ModelOuterFormWithModelForm(FormFieldSupportMixin, forms.Form):
    other_field = forms.CharField()
    form_field = ModelFormField(ModelInnerForm)


class ModelOuterFormWithModelFields(FormFieldSupportMixin, forms.Form):
    other_field = forms.CharField()
    form_field = ModelFormField(model=TestModel, fields=['field_0'])


class TestModelForm(forms.ModelForm):
    class Meta:
        model = TestModel
        fields = '__all__'


class CaseModelForm(ModelFormFieldSupportMixin, forms.ModelForm):
    application = ModelFormField('test.forms.ApplicationModelForm')

    class Meta:
        model = Case
        fields = '__all__'


class ApplicationModelForm(ModelFormFieldSupportMixin, forms.ModelForm):
    class Meta:
        model = Application
        fields = '__all__'


class TestCaseModelForm(ModelFormFieldSupportMixin, forms.ModelForm):
    non_rel_field = ModelFormField('test.forms.ApplicationModelForm')
    application = forms.CharField(max_length=255)

    class Meta:
        model = Case
        fields = '__all__'
