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


class BoundFormField(BoundField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._inner_form = None

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

    @property
    def inner_form(self):
        if self._inner_form is not None:
            return self._inner_form
        else:
            return self._get_form()

    def _get_form(self, **kwargs):
        # 需要加上is_bound判断
        # 如果不加，inner form会总是bounded
        # 就会影响unbounded情况下initial值的render
        kwargs['initial'] = self.initial
        if self.form.is_bound and 'data' not in kwargs:
            kwargs['data'] = self.form.data
        inner_form = self.field.get_form(**kwargs)
        self._inner_form = inner_form
        return inner_form

    def value(self):
        return self.inner_form

    @property
    def initial(self):
        value = copy.copy(self.field.initial) if self.field.initial is not None else {}
        value.update(self.form.initial.get(self.name, {}))
        return value

    def as_widget(self, widget=None, attrs=None, only_initial=False, using_template=None, template_name=None):
        if using_template is None:
            using_template = self.field.using_template or False

        if template_name is None:
            template_name = self.field.template_name

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

    def _get_form(self, **kwargs):
        kwargs['instance'] = self.instance
        return super()._get_form(**kwargs)

    @property
    def instance(self):
        # 在inner_form实例化之前，从outer_form的instance获取instance
        # 或者在ModelFormField上获取instance

        # 考虑到outer form不是ModelForm的情况，
        # 这种情况下outer form没有instance属性
        outer_form_intance = getattr(self.form, 'instance', None)
        if outer_form_intance is None:
            return self.field.instance
        instance = getattr(self.form.instance, self.name, None) or self.field.instance

        return instance

    def save(self, commit=False):
        # 默认情况下commit=False
        return self.inner_form.save(commit)


class BaseFormField(Field):
    widget = FormInput
    _base_class = None
    _bound_field_class = None

    def __init__(self, form_class=None, prefix=None, title=None,
                 using_template=False, template_name=None, **kwargs):
        self.title = title
        self.prefix = prefix
        self._form_class = form_class
        self.using_template = using_template
        self.template_name = template_name
        self._bound_field = None
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
            del self._form_class
            return form_class

        raise ImproperlyConfigured('form class configured improperly for {}'.format(self.__class__.__name__))

    def get_form(self, **kwargs):
        kwargs['prefix'] = self.prefix

        form = self.form_class(**kwargs)
        if not self.required:
            for field in form.fields.values():
                field.required = False

        if self.disabled:
            for field in form.fields.values():
                field.disabled = True

        return form

    def bind(self, form, field_name):
        self._bound_field = self._bound_field_class(form, self, field_name)

    @property
    def bound_field(self):
        return self._bound_field

    def get_bound_field(self, form=None, field_name=None):
        if self._bound_field is None:
            self._bound_field = self._bound_field_class(form, self, field_name)
        return self._bound_field

    def to_python(self, value):
        form = self.bound_field._get_form(data=value)
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
    _bound_field_class = BoundFormField


class ModelFormField(BaseFormField):
    _base_class = ModelForm
    _bound_field_class = BoundModelFormField

    def __init__(self, form_class=None, model=None, fields=None,
                 instance=None, **kwargs):
        self._model = model
        self.fields = fields
        self.instance = instance
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
        if self._model is None or not isinstance(self.fields, list) \
                or self.fields == []:
            raise ImproperlyConfigured('Must set form_class or model + fields')
        if not issubclass(self._model, Model):
            raise ImproperlyConfigured('model is not a Model subclass')
        try:
            form_class = modelform_factory(self._model, fields=self.fields)
        except AttributeError:
            raise ImproperlyConfigured('fields {} are improperly setted.'
                                       .format(self.fields))
        del self._form_class
        del self._model
        return form_class

    @cached_property
    def model(self):
        return self.form_class._meta.model

    def to_python(self, value):
        form = self.bound_field._get_form(data=value)
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
