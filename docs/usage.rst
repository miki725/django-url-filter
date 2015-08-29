Usage
=====

Vanilla
-------

In its simplest form, Django URL Filter usage resolves around ``FilterSet``s.
They can be used manually::

    from django import forms
    from url_filter.filter import Filter
    from url_filter.filtersets import FilterSet

    class ProfileFilterSet(FilterSet):
        lives_in_country = Filter(form_field=forms.CharField())

    class UserFilterSet(FilterSet):
        username = Filter(form_field=forms.CharField())
        email = Filter(form_field=forms.CharField())
        joined = Filter(form_field=forms.DateField())
        profile = ProfileFilterSet()

    query = QueryDict(
      'email__contains=gmail'
      '&joined__year=2015'
      '&profile__lives_in_country__iexact=us'
    )
    fs = UserFilterSet(data=query, queryset=User.objects.all())
    filtered_users = fs.filter()

Notable things to mention from above:

* ``FilterSet`` can be used as a ``Filter`` within another ``FilterSet``
  hence allowing filtering by related models.
* ``form_field`` is used to validate the filter value.
  Each lookup however can overwrite validation. For example ``year``
  lookup will use ``IntegerField`` rather then ``DateField``.

Django
------

Instead of manually creating ``FilterSet``, Django URL Filter comes with
``ModelFilterSet`` which greatly simplifies the task::


    from django import forms
    from url_filter.filtersets import ModelFilterSet

    class UserFilterSet(ModelFilterSet):
        class Meta(object):
            model = User
            fields = ['username', 'email', 'joined', 'profile']

Notable things:

* ``fields`` can actually be completely omitted. In that case
  ``FilterSet`` will use all fields available in the model, including
  related fields.
* filters can be manually overwritten when custom behavior is required::

    class UserFilterSet(ModelFilterSet):
        username = Filter(form_field=forms.CharField(max_length=15))

        class Meta(object):
            model = User
            fields = ['username', 'email', 'joined', 'profile']

Integrations
------------

Django URL Filters tries to be usage-agnostic and does not assume
how ``FilterSet`` is being used in the application. It does however
ship with some common integrations to simplify common workflows.

Django REST Framework
+++++++++++++++++++++

Django URL Filter can rather easily be integrated with DRF.
For that, a DRF filter backend is implemented and can be used in settings::

    # settings.py
    REST_FRAMEWORK = {
        'DEFAULT_FILTER_BACKENDS': [
            'url_filter.integrations.drf.DjangoFilterBackend',
        ]
    }

or manually set in the viewset::

    class MyViewSet(ModelViewSet):
        queryset = MyModel.objects.all()
        serializer_class = MyModelSerializer
        filter_backends = [DjangoFilterBackend]
        filter_fields = ['field1', 'field2']

Note in the example above, fields to be filtered on are explicitly
specified in the ``filter_fields`` attribute. Alternatively if more
control over ``FilterSet`` is required, it can be set explicitly::

    class MyFilterSet(FilterSet):
        pass

    class MyViewSet(ModelViewSet):
        queryset = MyModel.objects.all()
        serializer_class = MyModelSerializer
        filter_backends = [DjangoFilterBackend]
        filter_class = MyFilterSet

Backends
--------

``FilterSet`` by itself is decoupled from the actual filtering
of the queryset. Backend can be swapped by using ``filter_backend_class``::

    class FooFilterSet(FilterSet):
        filter_backend_class = MyFilterBackend

.. note::
  Currently only ``DjangoFilterBackend`` is implemented which uses
  Django ORM however more backends are planned for.
