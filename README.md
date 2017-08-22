django-formfield-utils
======================

A simple utils for Django FormField

- [示例 Simple FormField](http://demo.resettingmq.top/formfield/)
- [示例 Model FormField](http://demo.resettingmq.top/formfield/model/)


安装
----------------------
将form_field_utils包复制到项目文件夹下，并将form_field_utils添加到INSTALLED_APPS中。

> todo: 通过setup.py安装

开始
----------------------

### FormField

1. 声明内层子Form。

```python
from django import forms

class InnerForm(forms.Form):
    field_0 = forms.CharField(max_length=100)
```

2. 声明外层Form，通过`FormField.Fields.FormField`声明指向内层Form的from-field。

```python
from formfiled.forms import FormFieldSupportMixin
from formfield.fields import FormField

class OuterForm(FormFieldSupportMixin, forms.Form):
    field_outer = forms.CharField(max_length=100)
    formfield = FormField(InnerForm)
```

3. 将View中实例化外层Form，并且将外层Form实例传入template context。

4. 在template中对外层Form实例进行渲染。
```djangotemplate
{{ form.as_table}}
```

### ModelFormField

内层Form可以是Django ModelForm。

> *目前仅支持将`reverse OneToOneRel`类型的Field设置为ModelFormField。*

1. 声明Django Model。

```python
from django.db import models

class Order(models.Model):
    name = models.CharField('订单名', max_length=100)
    

class Contract(models.Model):
    serial_no = models.CharField('合同号', max_length=100)
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
```

2. 声明内层ModelForm

```python
from django import forms

class ContractModelForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = '__all__'
```

3. 声明外层ModelForm。

```python
from formfield.forms import ModelFormFieldSupportMixin
from formfield.fields import ModelFormField

class OrderModelForm(ModelFormFieldSupportMixin, forms.ModelForm):
    contract = ModelFormField(ContractModelForm)
    
    class Meta:
        model = Order
        fields = '__all__'
```

4. 类似于Simple FormField的使用，在View中生成外层Form的实例传入template context，并在template中对Form实例进行渲染。

5. 在View中对外成Form实例调用`save()`方法，能够保存外层对象实例以及内层对象实例，并正确关联两者关系。

选项
----------------------

### `title`选项

`title`选项用于指定FormField的标题，使得能够在渲染的时候打印。

默认`title`选项为None。

```python
class OrdereModelForm(ModelFormFieldSupportMixin, forms.ModelForm):
    contract = ModelFormField(
        ContractModelForm,
        title='关联合同'
    )
```

### `prefix`选项

通过`prefix`选项，能够指定内层Form的`prefix`属性，以避免内外层Form在HTML表单中`name`属性名和`id`属性名冲突。

```python
class OrdereModelForm(ModelFormFieldSupportMixin, forms.ModelForm):
    contract = ModelFormField(
        ContractModelForm,
        prefix='contract'
    )
```

### `using_template`选项

如果`using_template`为`False`，在template渲染FormField实例时(`{{ form_field }}`)会简单的调用内层`form.as_table()`方法。
如果`using_template`为`True`，则会按照内层FormField`template_name`指定的template对内层Form实例进行渲染。

`using_template`默认为`False`。

### `template_name`选项

当`using_template`为`True`的情况下，会根据`template_name`指定的template对内层Form对象进行渲染。
如果没有指定`template_name`，django-formfield-utils会使用自带的template对内层Form对象进行渲染。

```python
class OrdereModelForm(ModelFormFieldSupportMixin, forms.ModelForm):
    contract = ModelFormField(
        ContractModelForm,
        using_template=True,
        template_name='path/to/template'
    )
```

简易的外层Form template代码示例如下：

```djangotemplate
{# simple template code of rendering outer form #}
{% load formfield_widget %}

{% for field in form %}
    {% if field|is_formfield %}
        {# just call __str__() method of formfield #}
        {# so that can using template_name specified template #}
        {# to render the inner form of the formfield #}
        {{ field }}
    {% else %}
        {# render regular field here #}
    {% endif %}
{% endfor %}
```

这里使用了django-formfield-utils自带的`formfield_field.is_formfield` filter，
在template中判断一个field是否是FormField。

> todo: 增加设定全局FormField template的功能
