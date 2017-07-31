# -*- coding: utf-8 -*-

from django.db import models


class TestModel(models.Model):
    field_0 = models.CharField(max_length=100)
    field_1 = models.CharField(max_length=100, blank=True)


class Case(models.Model):
    name = models.CharField(max_length=255)


class Application(models.Model):
    no = models.CharField(max_length=255)
    case = models.OneToOneField(Case, null=True, blank=True)
