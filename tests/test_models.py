from datetime import timedelta
import json
import types

import diffs
from diffs.helpers import precise_timestamp
from diffs.models import Diff
from diffs.settings import diffs_settings

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from .mixins import TestModeMixin
from .models import TestModel


class DiffModelTestCase(TestCase):

    def test_data(self):
        """Asserts that data can be a json_str or dict and it will be handled correctly"""

        diff = Diff(data={'test': 'data'})

        self.assertEqual(diff.data, {'test': 'data'})

        diff = Diff(data=json.dumps({'test': 'data'}))

        self.assertEqual(diff.data, {'test': 'data'})


class DiffModelManagerTestCase(TestCase):

    def setUp(self):
        self.connection = diffs.get_connection()

    def tearDown(self):
        self.connection.flushdb()

    @classmethod
    def setUpClass(cls):
        # Register the class with diffs
        diffs.register(TestModel)
        super(DiffModelManagerTestCase, cls).setUpClass()

    def _get_family(self):
        """Helper method that returns a child and connected parent"""
        parent = TestModel.objects.create(name='parent')
        child = TestModel.objects.create(name='child')

        def get_diff_parent(self):
            return parent

        child.get_diff_parent = types.MethodType(get_diff_parent, child)

        return child, parent

    def test_model_save(self):
        """Asserts the signals are connected and diffs are created when expected."""

        tm = TestModel(name='Example')
        tm.save()

        # It should create a diff
        self.assertEqual(len(TestModel.diffs.get_by_object_id(tm.id)), 1)

        tm.name = 'example'
        tm.save()

        # It should create a diff
        self.assertEqual(len(tm.diffs), 2)

        tm.name = 'example'
        tm.save()

        # It should not create a diff
        self.assertEqual(len(TestModel.diffs.get_by_object_id(tm.id)), 2)

    def test_serialize_diff(self):
        """Asserts the serialize_diff method is called when available and the data is persisted."""

        def serialize_diff(self, dirty_fields):
            return {'test': 'data', 'fields': dirty_fields}

        tm = TestModel.objects.create(name='Example')

        self.assertEqual(len(TestModel.diffs.get_by_object_id(tm.id)), 1)

        # Add the method to the instance
        tm.serialize_diff = types.MethodType(serialize_diff, tm)

        tm.name = 'test'
        tm.save()

        # It should create a diff
        self.assertEqual(len(TestModel.diffs.get_by_object_id(tm.id)), 2)

        # It should have expected data
        expected = {'test': 'data', 'fields': ['name']}

        diff = TestModel.diffs.get_by_object_id(tm.id)[-1]

        self.assertEqual(expected, diff.data)

    def test_get_diff_parent(self):
        """Asserts the get_diff_parent method is called when available and data is persisted."""

        child, parent = self._get_family()

        child.name = 'child2'
        child.save()

        diffs = TestModel.diffs.get_by_object_id(child.id)

        self.assertEqual(len(diffs), 1)
        # It should save the diff under the parent
        parent_diffs = TestModel.diffs.get_by_object_id(parent.id)

        self.assertEqual(len(parent_diffs), 2)


class PruneDiffTestCase(TestCase):

    def setUp(self):
        self.connection = diffs.get_connection()

    def tearDown(self):
        self.connection.flushdb()

    def test_elements(self):
        """Asserts that elements are removed when expected."""

        current_age = precise_timestamp()

        self.connection.zadd('test', 'one', current_age)

        old_age = precise_timestamp(dt=timezone.now() - timedelta(seconds=diffs_settings['max_element_age'] + 1))

        self.connection.zadd('test', 'two', old_age)

        call_command('prune_diffs')

        # It should remove the old element
        self.assertEqual(self.connection.zcard('test'), 1)

    def test_non_sorted_set(self):
        """Asserts the command doesn't blow up when its not a sortedset"""
        self.connection.set('test', 'value')

        call_command('prune_diffs')


class FakeDiffModelManagerTestCase(TestModeMixin, DiffModelManagerTestCase):
    pass
