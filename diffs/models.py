import json

from django.utils.encoding import python_2_unicode_compatible
from redisco.containers import SortedSet
import six

from . import get_connection
from .helpers import precise_timestamp


@python_2_unicode_compatible
class Diff:
    """Model class that represents a single change to a model"""

    @classmethod
    def from_storage(cls, diff_str, timestamp):
        """Instantiates a diff object from a diff json str from redis"""
        diff = json.loads(diff_str.decode('utf-8'))
        return cls(diff['data'], diff['created'], timestamp)

    def __init__(self, data=None, created=None, timestamp=None):
        self.created = created

        if isinstance(data, six.string_types):
            data = json.loads(data)

        self.data = data

        if timestamp is None:
            timestamp = precise_timestamp()

        self.timestamp = timestamp

    def __str__(self):
        return "<{} {}>".format(self.__class__.__name__, self.data)

    def typecast_for_storage(self):
        """Returns a tuple of the (diff_str, score) for redis"""
        return json.dumps({'data': self.data, 'created': self.created}), self.timestamp


class DiffSortedSet(SortedSet):
    """SortedSet wrapper class that implements iterator methods to return Diff objects."""

    def __iter__(self):
        return iter([Diff.from_storage(item[0], item[1]) for item in self.zrange(0, -1, withscores=True)])

    def __reversed__(self):
        return iter([Diff.from_storage(item[0], item[1]) for item in self.zrevrange(0, -1, withscores=True)])


class DiffModelManager:
    """Manager class that wraps a DiffSortedSet with a django-like interface"""

    def __init__(self):
        self.model = None
        self.db = get_connection()

    def _generate_key(self, pk, model_cls=None):
        model = model_cls or self.model
        return '{}-{}'.format(model.__name__, str(pk))

    def contribute_to_class(self, model_cls, name):
        """Django hook to attach to model class."""
        self.model = model_cls
        setattr(model_cls, name, self)

    def get_sortedset(self, pk, model_cls=None):
        """Returns the SortedSet object"""
        key = self._generate_key(pk, model_cls=model_cls)
        return DiffSortedSet(key, self.db)

    def all(self, pk):
        """Returns a list of Diff objects for the given primary key."""
        return list(self.get_sortedset(pk))

    def create(self, data=None, created=None, pk=None, model_cls=None):
        """Create a new diff with the given params."""
        diff = Diff(data=data, created=created)
        self.get_sortedset(pk, model_cls=model_cls).zadd(*diff.typecast_for_storage())
        return diff
