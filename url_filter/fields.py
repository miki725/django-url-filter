# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from django import forms

from .validators import MaxLengthValidator, MinLengthValidator


class MultipleValuesField(forms.CharField):
    def __init__(self, child, min_values=2, max_values=None, delimiter=',',
                 *args, **kwargs):
        self.child = child
        self.delimiter = delimiter

        super(MultipleValuesField, self).__init__(*args, **kwargs)

        self.many_validators = []
        if min_values:
            self.many_validators.append(MinLengthValidator(min_values))
        if max_values:
            self.many_validators.append(MaxLengthValidator(max_values))

    def clean(self, value):
        value = self.to_python(value)
        self.validate(value)
        self.run_validators(value)

        if not value:
            return

        values = self.many_to_python(value)
        self.many_validate(values)
        self.many_run_validators(values)

        return values

    def many_to_python(self, value):
        return [self.child.clean(i) for i in value.split(self.delimiter)]

    def many_validate(self, values):
        pass

    def many_run_validators(self, values):
        if not values:
            return

        errors = []
        for v in self.many_validators:
            try:
                v(values)
            except forms.ValidationError as e:
                if hasattr(e, 'code') and e.code in self.error_messages:
                    e.message = self.error_messages[e.code]
                errors.extend(e.error_list)
        if errors:
            raise forms.ValidationError(errors)
