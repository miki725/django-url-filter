# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import inspect
from contextlib import contextmanager


class FilterSpec(object):
    """
    Class for describing filter specification.

    The main job of the :class:`.FilterSet` is to parse
    the submitted lookups into a list of filter specs.
    A list of these specs is then used by the filter backend
    to actually filter given queryset. That's what :class:`.FilterSpec`
    provides - a way to portably define filter specification
    to be used by a filter backend.

    The reason why filtering is decoupled from the :class:`.FilterSet`
    is because this allows to implement filter backends
    not related to Django.

    Attributes
    ----------
    components : list
        A list of strings which are names of the keys/attributes
        to be used in filtering of the queryset.
        For example lookup config with key
        ``user__profile__email`` will have components of
        ``['user', 'profile', 'email'].
    lookup : str
        Name of the lookup how final key/attribute from
        :attr:`.components` should be compared.
        For example lookup config with key
        ``user__profile__email__contains`` will have a lookup
        ``contains``.
    value
        Value of the filter.
    is_negated : bool, optional
        Whether this filter should be negated.
        By default its ``False``.
    filter_callable : func, optional
        Callable which should be used for filtering this
        filter spec. This is primaliry meant to be used
        by :class:`.CallableFilter`.
    """

    def __init__(
        self, components, lookup, value, is_negated=False, filter_callable=None
    ):
        self.components = components
        self.lookup = lookup
        self.value = value
        self.is_negated = is_negated
        self.filter_callable = filter_callable

    @property
    def is_callable(self):
        """
        Property for getting whether this filter specification is for a custom
        filter callable
        """
        return self.filter_callable is not None

    def __repr__(self):
        if self.is_callable:
            callable_repr = " via {}.{}".format(
                self.filter_callable.__self__.__class__.__name__,
                self.filter_callable.__name__,
            )
        else:
            callable_repr = ""

        return "<{name} {components} {negated}{lookup} {value!r}{callable}>".format(
            name=self.__class__.__name__,
            components=".".join(self.components),
            negated="NOT " if self.is_negated else "",
            lookup=self.lookup,
            value=self.value,
            callable=callable_repr,
        )

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash(repr(self))


class LookupConfig(object):
    """
    Lookup configuration which is used by :class:`.FilterSet`
    to create a :class:`.FilterSpec`.

    The main purpose of this config is to allow the use
    if recursion in :class:`.FilterSet`. Each lookup key
    (the keys in the querystring) is parsed into
    a nested one-key dictionary which lookup config stores.

    For example the querystring::

        ?user__profile__email__endswith=gmail.com

    is parsed into the following config::

        {
            'user': {
                'profile': {
                    'email': {
                        'endswith': 'gmail.com'
                    }
                }
            }
        }

    Attributes
    ----------
    key : str
        Full lookup key from the querystring.
        For example ``user__profile__email__endswith``
    data : dict, str
        Either:

        * nested dictionary where the key is the next key within
          the lookup chain and value is another :class:`.LookupConfig`
        * the filtering value as provided in the querystring value

    Parameters
    ----------
    key : str
        Full lookup key from the querystring.
    data : dict, str
        A regular vanilla Python dictionary.
        This class automatically converts nested
        dictionaries to instances of :class:`.LookupConfig`.
        Alternatively a filtering value as provided
        in the querystring.
    """

    def __init__(self, key, data):
        if isinstance(data, dict):
            data = {k: self.__class__(key, v) for k, v in data.items()}

        self.key = key
        self.data = data

    def is_key_value(self):
        """
        Check if this :class:`.LookupConfig` is not a nested :class:`.LookupConfig`
        but instead the value is a non-dict value.
        """
        return len(self.data) == 1 and not isinstance(self.value, dict)

    @property
    def name(self):
        """
        If the ``data`` is nested :class:`.LookupConfig`,
        this gets its first lookup key.
        """
        return next(iter(self.data.keys()))

    @property
    def value(self):
        """
        If the ``data`` is nested :class:`.LookupConfig`,
        this gets its first lookup value which could either
        be another :class:`.LookupConfig` or actual filtering value.
        """
        return next(iter(self.data.values()))

    def as_dict(self):
        """
        Converts the nested :class:`.LookupConfig` to a regular ``dict``.
        """
        if isinstance(self.data, dict):
            return {k: v.as_dict() for k, v in self.data.items()}
        return self.data

    def __repr__(self):
        return "<{} {}=>{}>".format(
            self.__class__.__name__, self.key, repr(self.as_dict())
        )


class SubClassDict(dict):
    """
    Special-purpose ``dict`` with special getter for looking up
    values by finding matching subclasses.

    This is better illustrated in an example::

        >>> class Klass(object): pass
        >>> class Foo(object): pass
        >>> class Bar(Foo): pass
        >>> mapping = SubClassDict({
        ...     Foo: 'foo',
        ...     Klass: 'klass',
        ... })
        >>> print(mapping.get(Klass))
        klass
        >>> print(mapping.get(Foo))
        foo
        >>> print(mapping.get(Bar))
        foo
    """

    def get(self, k, d=None):
        """
        If no value is found by using Python's default implementation,
        try to find the value where the key is a base class of the
        provided search class.
        """
        value = super(SubClassDict, self).get(k, d)

        # try to match by value
        if value is d and inspect.isclass(k):
            for klasses, v in self.items():
                if not isinstance(klasses, (list, tuple)):
                    klasses = [klasses]
                for klass in klasses:
                    if inspect.isclass(klass) and issubclass(k, klass):
                        return v

        return value


def dictify(obj):
    """
    Convert any object to a dictionary.

    If the given object is already an instance of a dict,
    it is directly returned. If not, then all the public
    attributes of the object are returned as a dict.
    """
    if isinstance(obj, dict):
        return obj
    else:
        return {k: getattr(obj, k) for k in dir(obj) if not k.startswith("_")}


def dict_pop(key, d):
    """
    Pop key from dictionary and return updated dictionary
    """
    d.pop(key, None)
    return d


@contextmanager
def suppress(e):
    """
    Suppress given exception type

    For example::

        >>> with suppress(ValueError):
        ...     print('test')
        ...     raise ValueError
        test
    """
    try:
        yield
    except e:
        pass
