# -*- coding: utf-8 -*-

from django.db import models


class TestModel(models.Model):
    field_0 = models.CharField(max_length=100)
    field_1 = models.CharField(max_length=100, blank=True)

    class Meta:
        abstract = True
