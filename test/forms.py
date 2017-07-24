# -*- coding: utf-8 -*-

from django import forms
from form_field_utils.fields import FormField, ModelFormField


from .models import TestModel


class InnerForm(forms.Form):
    inner_field = forms.CharField()
    inner_field_with_initial = forms.CharField(initial='inner form field initial', required=False)
    inner_field_with_inner_form_initial = forms.CharField()
    inner_field_with_outer_form_initial = forms.CharField()


class OuterForm(forms.Form):
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


class ModelOuterFormWithModelForm(forms.Form):
    other_field = forms.CharField()
    form_field = ModelFormField(ModelInnerForm)


class ModelOuterFormWithModelFields(forms.Form):
    other_field = forms.CharField()
    form_field = ModelFormField(model=TestModel, fields=['field_0'])

