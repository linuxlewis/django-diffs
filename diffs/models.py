import json

from django.utils.encoding import python_2_unicode_compatible
import six

from . import get_connection
from .helpers import precise_timestamp


@python_2_unicode_compatible
class Diff(object):
    """Model class that represents a single change to a model"""

    @classmethod
    def from_storage(cls, diff_str, timestamp=None):
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


class DiffSortedSet(object):
    """
    Simple class that represents a single SortedSet in redis.

    By default it returns diff objects.
    """

    def __init__(self, key, db):
        self.key = key
        self.db = db

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self.zrange(index.start, index.stop)
        else:
            return self.zrange(index, index)[0]

    def __iter__(self):
        return iter(self.zrange(0, -1, withscores=True))

    def __reversed__(self):
        return iter(self.zrevrange(0, -1, withscores=True))

    def _process_response(self, iterable):
        response = []
        for item in iterable:

            if isinstance(item, (list, tuple)):
                diff = Diff.from_storage(item[0], item[1])
            else:
                diff = Diff.from_storage(item)

            response.append(diff)
        return response

    @property
    def min_score(self):
        """
        Returns the minimum score in the SortedSet.
        """
        try:
            return self.zscore(self.db.zrange(self.key, 0, 0)[0])
        except IndexError:
            return None

    @property
    def max_score(self):
        """
        Returns the maximum score in the SortedSet.
        """
        try:
            return self.zscore(self.db.zrange(self.key, -1, -1)[0])
        except IndexError:
            return None

    def zadd(self, members, score=1):
        _members = []
        if not isinstance(members, dict):
            _members = [members, score]
        else:
            for member, score in members.items():
                _members += [member, score]

        return self.db.zadd(self.key, *_members)

    def zrange(self, start, stop, withscores=False):
        return self._process_response(self.db.zrange(self.key, start, stop, withscores=withscores))

    def zrangebyscore(self, min, max, **kwargs):
        return self._process_response(self.db.zrangebyscore(self.key, min, max, **kwargs))

    def zrevrangebyscore(self, max, min, **kwargs):
        return self._process_response(self.db.zrevrangebyscore(self.key, max, min, **kwargs))

    def zrevrange(self, start, stop, **kwargs):
        return self._process_response(self.db.zrevrange(self.key, start, stop, **kwargs))

    def zscore(self, elem):
        return self.db.zscore(self.key, elem)


class DiffModelDescriptor(object):

    def __init__(self, manager):
        self.manager = manager

    def __get__(self, instance, owner):

        # if accessing from the class
        if instance is None:
            return self.manager

        return self.manager.get_by_object_id(instance.id)

    def contribute_to_class(self, model_cls, name):
        """Django hook to attach to model class."""
        self.manager.model = model_cls
        setattr(model_cls, name, self)


class DiffModelManager(object):
    """Manager class that wraps a DiffSortedSet with a django-like interface"""

    def __init__(self):
        self.model = None
        self.db = get_connection()

    def _generate_key(self, pk, model_cls=None):
        model = model_cls or self.model
        return '{}-{}'.format(model.__name__, str(pk))

    def get_sortedset(self, pk, model_cls=None):
        """Returns the SortedSet object"""
        key = self._generate_key(pk, model_cls=model_cls)
        return DiffSortedSet(key, self.db)

    def get_by_object_id(self, pk):
        return list(self.get_sortedset(pk))

    def create(self, data=None, created=None, pk=None, model_cls=None, timestamp=None):
        """Create a new diff with the given params."""
        diff = Diff(data=data, created=created, timestamp=timestamp)
        self.get_sortedset(pk, model_cls=model_cls).zadd(*diff.typecast_for_storage())
        return diff
