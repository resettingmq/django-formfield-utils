# -*- coding: utf-8 -*-

import copy
import warnings

from django.forms.fields import Field, BoundField
from django.forms import Form, ModelForm, modelform_factory
from django.utils.module_loading import import_string
from django.core.exceptions import ImproperlyConfigured, ValidationError, FieldError
from django.utils.functional import cached_property
from django.utils.deprecation import RemovedInDjango21Warning
from django.utils.inspect import func_accepts_kwargs, func_supports_parameter
from django.db.models import Model

from .widgets import FormInput


class BaseFormField(Field):
    widget = FormInput
    _base_class = None

    def __init__(self, form_class=None, prefix=None, title=None,
                 using_template=False, template_name=None, **kwargs):
        self.title = title
        self.prefix = prefix
        self._form_class = form_class
        self.using_template = using_template
        self.template_name = template_name
        # self._inner_form = None
        super().__init__(**kwargs)

        if self.initial is None:
            self.initial = {}

    @cached_property
    def form_class(self):
        form_class = self._form_class
        if isinstance(form_class, str):
            try:
                form_class = import_string(form_class)
            except ImportError:
                raise ImproperlyConfigured('Can not import {}'.format(form_class))
        if issubclass(form_class, self._base_class):
            return form_class

        raise ImproperlyConfigured('form class configured improperly for {}'.format(self.__class__.__name__))

    def get_form(self, data=None, initial=None, **kwargs):
        # if self._inner_form is not None:
        #     print(id(self._inner_form))
        #     # print(self._inner_form.data)
        #     return self._inner_form

        kwargs['data'] = data
        kwargs['initial'] = initial
        kwargs['prefix'] = self.prefix

        form = self.form_class(**kwargs)
        if not self.required:
            for field in form.fields.values():
                field.required = False

        if self.disabled:
            for field in form.fields.values():
                field.disabled = True

        # self._inner_form = form
        # print(id(self._inner_form))
        # # print(self._inner_form.data)
        return form

    def get_bound_field(self, form, field_name):
        return BoundFormField(form, self, field_name)

    def to_python(self, value):
        form = self.get_form(value)
        if form.is_valid():
            return form.cleaned_data

        # 将inner_form的errors转化为不带error_dict属性的ValidationError对象
        new_error_list = []
        for name, error_list in form.errors.as_data().items():
            for error in error_list:
                if hasattr(error, 'message'):
                    error.message = 'Field {} in FormField: {}'.format(name, error.message)
            new_error_list.extend(error_list)
        raise ValidationError(new_error_list, code='FormFieldError')


class FormField(BaseFormField):
    _base_class = Form


class ModelFormField(BaseFormField):
    _base_class = ModelForm

    def __init__(self, form_class=None, model=None, fields=None,
                 instance=None, **kwargs):
        self.model = model
        self.fields = fields
        self._instance = instance
        super().__init__(form_class, **kwargs)

    @cached_property
    def form_class(self):
        form_class = self._form_class
        if isinstance(form_class, str):
            try:
                form_class = import_string(form_class)
            except ImportError:
                raise ImproperlyConfigured('Can not import {}'.format(form_class))
        if isinstance(form_class, type) and issubclass(form_class, self._base_class):
            return form_class
        if self.model is None or not isinstance(self.fields, list) \
                or self.fields == []:
            raise ImproperlyConfigured('Must set form_class or model + fields')
        if not issubclass(self.model, Model):
            raise ImproperlyConfigured('model is not a Model subclass')
        try:
            form_class = modelform_factory(self.model, fields=self.fields)
        except AttributeError:
            raise ImproperlyConfigured('fields {} are improperly setted.'
                                       .format(self.fields))
        return form_class

    def get_form(self, data=None, initial=None, instance=None, **kwargs):
        if instance is None:
            instance = self.instance
        kwargs.update(instance=instance)
        return super().get_form(data, initial, **kwargs)

    def to_python(self, value):
        form = self.get_form(value, instance=self.instance)
        if form.is_valid():
            return form.cleaned_data

        # 将inner_form的errors转化为不带error_dict属性的ValidationError对象
        new_error_list = []
        for name, error_list in form.errors.as_data().items():
            for error in error_list:
                if hasattr(error, 'message'):
                    error.message = 'Field {} in FormField: {}'.format(name, error.message)
            new_error_list.extend(error_list)
        raise ValidationError(new_error_list, code='FormFieldError')

    def get_bound_field(self, form, field_name):
        return BoundModelFormField(form, self, field_name)

    @property
    def instance(self):
        return self._instance

    @instance.setter
    def instance(self, value):
        self._instance = value


class BoundFormField(BoundField):
    def __getitem__(self, name):
        return self.inner_form[name]

    def __iter__(self):
        return iter(self.inner_form)

    @property
    def data(self):
        # 委托到inner form各field上取值
        # 对于多层嵌套的FormField实现了递归取值
        # 而不需要在POST数据中根据键来构建dict（需要实现递归逻辑）
        return {name: self.inner_form[name].data for name in self.inner_form.fields}

    @property
    def fields(self):
        return self.inner_form.fields

    @cached_property
    def inner_form(self):
        # 需要加上is_bound判断
        # 如果不加，inner form会总是bounded
        # 就会影响unbounded情况下initial值的render
        if self.form.is_bound:
            return self.field.get_form(self.form.data, self.initial)
        return self.field.get_form(initial=self.initial)

    def value(self):
        return self.inner_form

    @property
    def initial(self):
        value = copy.copy(self.field.initial)
        value.update(self.form.initial.get(self.name, {}))
        return value

    def as_widget(self, widget=None, attrs=None, only_initial=False, using_template=None, template_name=None):
        if using_template is None:
            using_template = self.field.using_template

        # 一下代码段为Django的源码
        if not widget:
            widget = self.field.widget

        if self.field.localize:
            widget.is_localized = True

        attrs = attrs or {}
        attrs = self.build_widget_attrs(attrs, widget)
        auto_id = self.auto_id
        if auto_id and 'id' not in attrs and 'id' not in widget.attrs:
            if not only_initial:
                attrs['id'] = auto_id
            else:
                attrs['id'] = self.html_initial_id

        if not only_initial:
            name = self.html_name
        else:
            name = self.html_initial_name

        kwargs = {}
        if func_supports_parameter(widget.render, 'renderer') or func_accepts_kwargs(widget.render):
            kwargs['renderer'] = self.form.renderer
        else:
            warnings.warn(
                'Add the `renderer` argument to the render() method of %s. '
                'It will be mandatory in Django 2.1.' % widget.__class__,
                RemovedInDjango21Warning, stacklevel=2,
            )
        return widget.render(
            name=name,
            value=self.value(),
            attrs=attrs,
            context=self.get_render_context(),
            using_template=using_template,
            template_name=template_name,
            **kwargs
        )

    def get_render_context(self):
        context = {'title': self.field.title}
        return context


class BoundModelFormField(BoundFormField):
    #
    # @cached_property
    # def inner_form(self):
    #     # print('in modelform: ', id(self))
    #     if self.form.is_bound:
    #         # print('bound form: ', id(self.form))
    #         # print('form data: ', self.form.data)
    #         # print('instance: ', self.field.instance.field_0)
    #         return self.field.get_form(self.form.data, self.initial, self.field.instance)
    #     else:
    #         # print('unbound form: ', id(self.form))
    #         # print('form data: ', self.form.data)
    #         # print('instance: ', self.field.instance.field_0)
    #         return self.field.get_form(initial=self.initial, instance=self.field.instance)

    def save(self, commit=False):
        # 默认情况下commit=False
        return self.inner_form.save(commit)
