.. :changelog:

History
-------

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
