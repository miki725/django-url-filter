Big Picture
===========

This document explains all of the concepts used in Django URL Filter
in context hence providing a "big picture" of how it works.

Basics
------

In order to filter any data, this library breaks the process
to 3 phases:

1. Parse the URL querystring into ``LookupConfig``
2. Loop throught all the configs and generate ``FilterSpec`` when possible
3. Use the list of specs to actually filter data

And here is a bit more information about each phase.

Parsing
+++++++

Fundamentally a querystring is a collection of key-pairs.
As such, this data is natually flat and is usually represented
as a simple dictionary::

    ?foo=bar&happy=rainbows => {
        'foo': 'bar',
        'happy': 'rainbows',
    }

.. note::
  Technically this is not 100% true since key
  can be repeated which is why Django uses ``QueryDict`` but for
  the purposes of this discussion, lets assume no duplicate keys
  are present.

The filtering however is not flat. Each querystring key can be nested
when using nested ``FilterSet`` and in addition it can optionally
contain lookup. For example::

    ?foo=bar
    ?foo__contains=bar
    ?foo__nested=bar
    ?foo__nested__contains=bar
    ?foo__nested__othernested=bar
    ?foo__nested__othernested__contains=bar

In order to accomodate the nested structure of querystring keys,
Django URL Filter parses all querystring key-value pairs to
nested dictionaries. For example::

    ?foo__nested__othernested=bar => {
        'foo': {
            'nested': {
                'othernested': 'bar'
            }
        }
    }
    ?foo__nested__othernested__contains=bar => {
        'foo': {
            'nested': {
                'othernested': {
                    'contains': 'bar'
                }
            }
        }
    }

That is essentially what ``LookupConfig`` stores. Since these dictionaries
are flat (each dictionaty has at most one key), it also provides some utility
properties for dealing with such data. You can refer to the
:py:class:`url_filter.utils.LookupConfig` API documentation for more
information.

Filter Specification
++++++++++++++++++++

As mentioned in :doc:`README <index>`, Django URL Filter decouples parsing
of querystring and filtering. It achieves that by constructing filter
specifications which have all necessary information to filter data
without actually filtering data. Thats what ``FilterSpec`` is.
It stores 3 required pieces of information on how to filter data:

* Which attribute to filter on. Since models can be related by attributes
  related models, this actually ends up being a list of attributes which
  we call components.
* Lookup to use to filter data. This specifies how the value should be
  compared while doing filtering. Example is ``exact``, ``contains``.
  Currenlty only lookups from Django ORM are supported.
* If the filter is negated. For example to filter when username is ``'foo'``
  to filter when username is not ``'foo'``.

Filtering
+++++++++

Since filtering is decoupled from the ``FilterSet``, the filtering honors
all full on a specified filter backend. The backend is very simple.
It takes a list of filter specifications and a data to filter and its
job is to filter that data as specified in the specifications.

.. note::
  Currently we only support Django ORM filter backend but you can imagine
  that any backend can be implemented. We plan to add support for SQLAlchemy
  since, well, why not add it? Eventually filter backends can be added
  for flat data-structures like filtering a vanilla Python lists or
  filtering from exotic data-source like Mongo.

Steps
-----

Above information hopefully puts things in perspective and here is more
detailed step-by-step guide what Django URL Filter does behind the scenes:

#. ``FilterSet`` is instantiated with querystring data as well as
   querystring to filter.
#. ``FilterSet`` is asked to filter given data via
   :py:meth:`filter <url_filter.filtersets.base.FilterSet.filter>` method
   which kicks in all the steps below.
#. ``FilterSet`` finds all filters it is capable of Filtering
   via :py:meth:`get_filters <url_filter.filtersets.base.FilterSet.get_filters>`.
   This is where custom filtersets can hook into to do custom stuff like
   extracting filters from a Django model.
#. ``FilterSet`` binds all child filters to itself via
   :py:meth:`bind <url_filter.filters.Filter.bind>`.
   This practically sets :py:attr:`parent <url_filter.filters.Filter.parent>`
   and :py:attr:`name <url_filter.filters.Filter.name>`.
#. Root ``FilterSet`` loops through all querystring pairs and generates
   ``LookupConfig`` for all of them.
#. Root ``FilterSet`` loops through all generated configs and attemps to
   find appropriate filter to use to generate a spec fo the given config.
   The matching happens by the first key in the ``LookupConfig`` dict.
   If that key is found in available filters, that filer is used and
   otherwise that config is skipped. This is among the reasons why
   ``LookupConfig`` is used since it allows this step to be very simple.
#. If appropriate filter is found, it is passed nested config to the child
   filter which then goes through very similar process as in previous step
   until it gets to a leaf filter.
#. Leaf ``Filter`` gets the config. In then checks if the config is still
   nested. For example if the config is simply a value (e.g. ``'bar'``)
   or is still a dictionary (e.g. ``{'contains': 'bar'}``).
   If the config is just a value, it then uses a default lookup for that
   filter as provided in ``default_lookup`` parameter when instantiating
   ``Filter``. If the config is a dictionary, it makes sure that it is a
   valid lookup config (e.g. its not ``{'rainbows': {'contains': 'bar'}}``
   since it would not know what to do with ``rainbows`` since it is not a
   valid lookup value).
#. Now that ``Filter`` validated the lookup itself, it cleans the actual
   filter value by using either ``form_field`` as passed as parameter
   when instantiating ``Filter`` or by using loopup overwrite.
   Overwrites are necessary for more exotic lookups like ``in`` or ``year``
   since they need to validate data in a different way.
#. If the value is valid, then the leaf filter constructs a ``FilterSpec``
   since it has all the necessary information to do that - 1) all filter
   component names from all ancestors (e.g. all attributes which
   should be accessed on the queryset to get to the value to be filtered on);
   2) the actual filter value and 3) if the filter is negated.
#. At this point, root ``FilterSpec`` will get the ``FilterSpec`` as
   bubbled up from the leaf filter. If any ``ValidationError`` exceptions
   are raised, then depending on ``strict_mode``, it will either ignores
   errors or will propagate them up to the caller of the filterset.
#. Once all specs are collected from all the querystring key-value-pairs,
   root ``FilterSet`` instantiates a filter backend and passes it
   all the specs.
#. Finally root ``FilterSet`` uses the filter backend to filter
   given queryset and returns the results to the user.

Some important things to note:

* Root ``FilterSet`` does all the looping over querystring data and
  generated configurations.
* Children filters of a root ``FilterSet`` are only responsible for
  generating ``FilterSpec`` and in the process validating the data.
