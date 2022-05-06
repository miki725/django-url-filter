# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django import forms

from .validators import MaxLengthValidator, MinLengthValidator


class MultipleValuesField(forms.CharField):
    """
    Custom Django field for validating/cleaning multiple
    values given in a single value separated by a delimiter.

    Parameters
    ----------
    child : Field, optional
        Another Django form field which should be used.
    min_values : int, optional
        Minimum number of values which must be provided.
        By default at least 2 values are required.
    max_values : int, optional
        Maximum number of values which can be provided.
        By default no maximum is enforced.
    max_validators : list, optional
        Additional validators which should be used to validate
        all values once split by the delimiter.
    delimiter : str, optional
        The delimiter by which the value will be split into
        multiple values.
        By default ``,`` is used.
    all_valid : bool, optional
        When ``False``, if any specific item does not pass validation
        it is ignored without failing complete field validation.
        Default is ``True`` which enforces validation for all items.
    """

    def __init__(
        self,
        child=None,
        min_values=2,
        max_values=None,
        many_validators=None,
        delimiter=",",
        all_valid=True,
        *args,
        **kwargs
    ):
        self.child = child or forms.CharField()
        self.delimiter = delimiter
        self.all_valid = all_valid

        super(MultipleValuesField, self).__init__(*args, **kwargs)

        self.many_validators = many_validators or []
        if min_values:
            self.many_validators.append(MinLengthValidator(min_values))
        if max_values:
            self.many_validators.append(MaxLengthValidator(max_values))

    def clean(self, value):
        """
        Custom ``clean`` which first validates the value first by using
        standard ``CharField`` and if all passes, it applies
        similar validations for each value once its split.
        """
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
        """
        Method responsible to split the value into multiple
        values by using the delimiter and cleaning each one
        as per the child field.
        """
        values = []
        for i in value.split(self.delimiter):
            try:
                values.append(self.child.clean(i))
            except forms.ValidationError:
                if self.all_valid:
                    raise
        return values

    def many_validate(self, values):
        """
        Hook for validating all values.
        """
        if not values and self.required:
            raise forms.ValidationError(
                self.error_messages["required"], code="required"
            )

    def many_run_validators(self, values):
        """
        Run each validation from ``many_validators`` for the cleaned values.
        """
        if not values:
            return

        errors = []
        for v in self.many_validators:
            try:
                v(values)
            except forms.ValidationError as e:
                if hasattr(e, "code") and e.code in self.error_messages:
                    e = forms.ValidationError(
                        self.error_messages[e.code], e.code, e.params
                    )
                errors.extend(e.error_list)
        if errors:
            raise forms.ValidationError(errors)
