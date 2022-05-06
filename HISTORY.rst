.. :changelog:

History
-------

0.3.15 (2020-02-10)
~~~~~~~~~~~~~~~~~~~

* Fixes ``date`` lookup when using Django ORM.
  See `#92 <https://github.com/miki725/django-url-filter/issues/92>`_.

0.3.14 (2019-10-30)
~~~~~~~~~~~~~~~~~~~

* Using ``CharField`` for ``regex`` filters.
  See `#90 <https://github.com/miki725/django-url-filter/pull/90>`_.
* ``SQLAlchemyFilterBackend`` does not join models if already join path
  is partially joined already.
* ``SQLAlchemyFilterBackend`` joins when ``selectinjoin`` is used.

0.3.13 (2019-07-28)
~~~~~~~~~~~~~~~~~~~

* Fixing `iregex` documentation in DRF coreapi integration.

0.3.12 (2019-01-24)
~~~~~~~~~~~~~~~~~~~

* Adding support for ``FilterSet.Meta.fields == '__all__'`` which is useful in DRF integration.
  See `#39 <https://github.com/miki725/django-url-filter/pull/39>`_.

0.3.11 (2018-12-06)
~~~~~~~~~~~~~~~~~~~

* Not modifying queryset in Django backend if no filters were applied.
  See `#73 <https://github.com/miki725/django-url-filter/pull/73>`_.

0.3.10 (2018-11-14)
~~~~~~~~~~~~~~~~~~~

* Only running ``distinct`` on queryset when one of filters is on one-to-many relation.
  This should help with performance.
  See `#26 <https://github.com/miki725/django-url-filter/issues/26>`_.

0.3.9 (2018-11-12)
~~~~~~~~~~~~~~~~~~

* Adding ``iin`` form field overwrite for SQLAlchemy as otherwise by default
  ``iin`` lookup is not validated correctly.

0.3.8 (2018-08-08)
~~~~~~~~~~~~~~~~~~

* Fixed ``SQLAlchemyFilterBackend`` by not joining nested models
  when they are already eager loaded via ``query.options()``.

0.3.7 (2018-07-27)
~~~~~~~~~~~~~~~~~~

* Added ``StrictModel.empty`` which is new default.
  It returns empty queryset when any filter validations fail.
* Fixed ``in`` lookup. Previously if any of the items were invalid
  whole filter would fail and depending on strict mode would
  either return all results, no results or will raise exception.
  Now in ``StrictMode.empty`` and ``StrictMode.drop`` any invalid
  items are ignored which will filter results for valid items.
  See `#63 <https://github.com/miki725/django-url-filter/issues/64>`_.
* Added ability in ``ModelFilterSet`` to customize filter names
  by providing ``extra_kwargs`` with field ``source``.
  See `#66 <https://github.com/miki725/django-url-filter/issues/66>`_.

0.3.6 (2018-07-23)
~~~~~~~~~~~~~~~~~~

* Added support for ``extra_kwargs`` in ``ModelFilterSet.Meta``.
* Added ``CoreAPIURLFilterBackend`` which enables documented filters in swagger docs.
* Added ``iin`` lookup in plain and sqlalchemy backends.
* Fixing inconsistency between plain and Django ``week_day`` lookup.
  Now both are consistent with ``1``-Monday and ``7``-Sunday.

0.3.5 (2018-02-27)
~~~~~~~~~~~~~~~~~~

* Django 2 support.
* Using `tox-travis <https://github.com/tox-dev/tox-travis>`_ for travis builds.
* Fixed negated queries in Django backend.
  Previously negation did ``NOT (condition1 and condition2)`` vs expected
  ``NOT condition1 and NOT condition2``.
  See `#53 <https://github.com/miki725/django-url-filter/issues/53>`_.

0.3.4 (2017-08-17)
~~~~~~~~~~~~~~~~~~

* Py36 compatibility by switching to ``enum-compat`` from ``enum34``
* Improvement to ``README`` by including imports in code examples
* Defaulting ``SQLAlchemyModelFilterSet`` to use ``SQLAlchemyFilterBackend``
* Defaulting ``PlainModelFilterSet`` to use ``PlainFilterBackend``
* Using universal wheels for distribution

0.3.3 (2017-06-15)
~~~~~~~~~~~~~~~~~~

* Fixed bug which did not allow to use SQLAlchemy backend fully
  without having ``django.contrib.contenttypes`` in installed apps.
  See `#36 <https://github.com/miki725/django-url-filter/issues/36>`_.
* Improved SQLAlchemy versions compatibility.
* Added ``URLFilterBackend`` alias in DRF integration for backend to reduce
  confusion with ``DjangoFilterBackend`` as in url filter core backend.

0.3.2 (2017-05-19)
~~~~~~~~~~~~~~~~~~

* Fixed plain backend to return list in Python 3 vs ``filter()`` generator
  which is not compatible with Django pagination since it requires ``len()``
  to be implemented.

0.3.1 (2017-05-18)
~~~~~~~~~~~~~~~~~~

* Fixed bug where default filters were used in root filtersets.
  As a result additional querystring parameters were validation which
  broke other functionality such as pagination.

0.3.0 (2017-01-26)
~~~~~~~~~~~~~~~~~~

* Added plain objects filtering support.
  More in `docs <https://django-url-filter.readthedocs.io/en/latest/usage.html#plain-filtering>`_
  and GitHub issue `#8 <https://github.com/miki725/django-url-filter/issues/8>`_.
* Added `CallableFilter <https://django-url-filter.readthedocs.io/en/latest/api/django_ufilter.filters.html#django_ufilter.filters.CallableFilter>`_ which allows to implement custom filters.
* Normalizing to DRF's ``ValidationError`` when using ``StrictMode.Fail``
  since filterset raises Django's ``ValidationError`` which caused 500 status code.
* Fixes ``ModelFilterSet`` automatic introspection to ignore ``GenericForeignKey``
  since they dont have form fields associated with them.
  See `#20 <https://github.com/miki725/django-url-filter/issues/20>`_.
* Releasing with `wheels <http://pythonwheels.com/>`_.

0.2.0 (2015-09-12)
~~~~~~~~~~~~~~~~~~

* Added `SQLAlchemy <http://www.sqlalchemy.org/>`_ support.
* ``FilterSet`` instances have much more useful ``__repr__`` which
  shows all filters at a glance. For example::

    >>> PlaceFilterSet()
    PlaceFilterSet()
      address = Filter(form_field=CharField, lookups=ALL, default_lookup="exact", is_default=False)
      id = Filter(form_field=IntegerField, lookups=ALL, default_lookup="exact", is_default=True)
      name = Filter(form_field=CharField, lookups=ALL, default_lookup="exact", is_default=False)
      restaurant = RestaurantFilterSet()
        serves_hot_dogs = Filter(form_field=BooleanField, lookups=ALL, default_lookup="exact", is_default=False)
        serves_pizza = Filter(form_field=BooleanField, lookups=ALL, default_lookup="exact", is_default=False)
        waiter = WaiterFilterSet()
          id = Filter(form_field=IntegerField, lookups=ALL, default_lookup="exact", is_default=True)
          name = Filter(form_field=CharField, lookups=ALL, default_lookup="exact", is_default=False)

0.1.1 (2015-09-06)
~~~~~~~~~~~~~~~~~~

* Fixed installation issue where not all subpackages were installed.

0.1.0 (2015-08-30)
~~~~~~~~~~~~~~~~~~

* First release on PyPI.
