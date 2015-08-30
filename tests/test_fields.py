# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import pytest
from django import forms

from url_filter.fields import MultipleValuesField
from url_filter.validators import MaxLengthValidator, MinLengthValidator


class TestMultipleValuesField(object):
    def test_init(self):
        field = MultipleValuesField(
            child=forms.IntegerField(),
            min_values=2,
            max_values=100,
            delimiter=';'
        )

        assert isinstance(field.child, forms.IntegerField)
        assert field.delimiter == ';'
        assert any((isinstance(i, MinLengthValidator) for i in field.many_validators))
        assert any((isinstance(i, MaxLengthValidator) for i in field.many_validators))

    def test_clean_empty(self):
        assert MultipleValuesField(required=False).clean('') is None

    def test_clean(self):
        field = MultipleValuesField(min_values=2, max_values=3)

        assert field.clean('hello,world') == ['hello', 'world']

        with pytest.raises(forms.ValidationError):
            field.clean('hello')
        with pytest.raises(forms.ValidationError):
            field.clean('hello,world,and,many,happy,rainbows')

    def test_many_to_python(self):
        field = MultipleValuesField()

        assert field.many_to_python('hello,world') == ['hello', 'world']

    def test_many_validate(self):
        assert MultipleValuesField().many_validate('') is None

    def test_many_run_validators(self):
        field = MultipleValuesField(error_messages={'min_length': 'foo'})

        assert field.many_run_validators(None) is None

        with pytest.raises(forms.ValidationError) as e:
            field.many_run_validators(['hello'])
        assert e.value.error_list[0].message == 'foo'
