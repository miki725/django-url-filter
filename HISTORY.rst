.. :changelog:

History
-------

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
* Added `CallableFilter <https://django-url-filter.readthedocs.io/en/latest/api/url_filter.filters.html#url_filter.filters.CallableFilter>`_ which allows to implement custom filters.
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
