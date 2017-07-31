# -*- coding: utf-8 -*-

import copy
from collections import OrderedDict

from django.forms.forms import DeclarativeFieldsMetaclass
from django.forms.models import ModelFormMetaclass
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db import transaction
from django.forms.utils import ErrorList

from .fields import BaseFormField, FormField, ModelFormField


class FormFieldSupportFormMeta(DeclarativeFieldsMetaclass):
    def __new__(mcls, name, bases, attrs):
        new_class = super().__new__(mcls, name, bases, attrs)

        form_fields = []
        for name, field in new_class.declared_fields.items():
            if isinstance(field, BaseFormField):
                form_fields.append((name, field))

        new_class.form_fields = OrderedDict(form_fields)

        return new_class


class FormFieldSupportMixin(metaclass=FormFieldSupportFormMeta):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name in self.form_fields:
            # 绑定BoundFormField实例到fields[xxx]
            self.fields[name].bind(self, name)


class ModelFormFieldSupportModelFormMeta(FormFieldSupportFormMeta, ModelFormMetaclass):
    def __new__(mcls, name, bases, attrs):
        new_class = super().__new__(mcls, name, bases, attrs)
        opts = new_class._meta
        model = opts.model
        if model is None:
            return new_class

        modelform_fields = []
        for fname, field in new_class.form_fields.items():
            # 搜索OneToOneRel对应的ModelFormField
            try:
                model_field = model._meta.get_field(fname)
            except FieldDoesNotExist:
                continue
            if model_field.one_to_one and not model_field.concrete and\
                    isinstance(field, ModelFormField):
                # if model_field.related_model is not field.model:
                #     raise ImproperlyConfigured('model not match for field {}.{}'
                #                                .format(name, fname))
                modelform_fields.append((fname, field))
        new_class.modelform_fields = OrderedDict(modelform_fields)

        return new_class


class ModelFormFieldSupportMixin(FormFieldSupportMixin,
                                 metaclass=ModelFormFieldSupportModelFormMeta):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        outer_model = self._meta.model
        outer_opts = outer_model._meta
        for name in self.modelform_fields:
            inner_opts = self.fields[name].model._meta

            # 用于判断inner ModelForm的model是否outer model相匹配
            if outer_opts.get_field(name).related_model is not inner_opts.model:
                raise ImproperlyConfigured(
                    'model: {} not match for field {}.{}'.format(
                        inner_opts.model.__name__,
                        self.__class__.__name__,
                        name
                    )
                )

            # 用于删除inner form指向outer model的field
            for inner_field_name in list(self[name].inner_form.fields):
                if inner_opts.get_field(inner_field_name).related_model is outer_model:
                    self[name].inner_form.fields.pop(inner_field_name)

    # @transaction.atomic
    def save(self, commit=True):

        outer_obj = super().save(commit=commit)
        self.save_related(commit=commit)

        return outer_obj

    def save_related(self, commit=True):
        # 建立inner instance和outer instance的关系
        for name in self.modelform_fields:
            setattr(self.instance, name, self[name].inner_form.instance)
            self[name].save(commit=commit)


