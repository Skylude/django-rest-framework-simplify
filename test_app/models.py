from django.db import models

from rest_framework_simplify.models import SimplifyModel
from rest_framework_simplify.fields import SimplifyEncryptedCharField


class BasicClass(SimplifyModel):
    CACHE = True
    CACHE_TIME = 15

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=15)
    active = models.BooleanField(null=False, default=True)
    child_one = models.OneToOneField('ChildClass', null=True, blank=True, related_name='basic_class_one')
    child_two = models.OneToOneField('ChildClass', null=True, blank=True, related_name='basic_class_two')
    exclude_field = models.CharField(max_length=25, null=True, blank=True)
    child_three = models.ManyToManyField('ChildClass', null=True, blank=True, related_name='basic_class_three')

    @property
    def test_prop(self):
        return True

    @staticmethod
    def get_filters():
        return {
            'active': {
                'type': bool,
                'list': False
            },
            'test_prop': {
                'type': bool,
                'list': False,
                'property': True
            },
            'child_three__id__contains_all': {
                'type': int,
                'list': True
            }
        }

    @staticmethod
    def get_includes():
        return ['child_one__id', 'child_three']

    @staticmethod
    def get_excludes():
        return ['exclude_field']


class ChildClass(SimplifyModel):
    CACHE = True

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=15)


class LinkingClass(SimplifyModel):
    id = models.AutoField(primary_key=True)
    basic_class = models.ForeignKey('BasicClass', null=False, related_name='linking_classes')
    child_class = models.ForeignKey('ChildClass', null=False, related_name='linking_classes')


class MetaDataClass(SimplifyModel):
    CHOICE_1 = 'one'
    CHOICE_2 = 'two'
    CHOICE_3 = 'three'
    CHOICES = (
        (CHOICE_1, 'One'),
        (CHOICE_2, 'Two'),
        (CHOICE_3, 'Three'),
    )
    id = models.AutoField(primary_key=True)
    choice = models.CharField(max_length=32, choices=CHOICES, default=CHOICE_2)


class EncryptedClass(SimplifyModel):
    id = models.AutoField(primary_key=True)
    encrypted_val = SimplifyEncryptedCharField(max_length=256, display_chars=-4)


class OneToOneClass(SimplifyModel):
    alternative_id = models.IntegerField(primary_key=True)


class RequestFieldSaveClass(SimplifyModel):
    REQUEST_FIELDS_TO_SAVE = [('method', 'method')]

    id = models.AutoField(primary_key=True)
    method = models.CharField(max_length=32, null=False, blank=False)