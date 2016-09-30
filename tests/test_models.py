import types

import diffs
from django.test import TestCase

from .models import TestModel


class DiffTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        # Register the class with diffs
        diffs.register(TestModel)
        super(DiffTestCase, cls).setUpClass()

    def _get_family(self):
        """Helper method that returns a child and connected parent"""
        parent = TestModel.objects.create(name='parent')
        child = TestModel.objects.create(name='child')

        def get_parent_object(self):
            return parent

        child.get_parent_object = types.MethodType(get_parent_object, child)

        return child, parent

    def test_model_save(self):
        """Asserts the signals are connected and diffs are created when expected."""

        tm = TestModel(name='Example')
        tm.save()

        # It should create a diff
        self.assertEqual(TestModel.diffs.get_diffs(tm.id).count(), 1)

        tm.name = 'example'
        tm.save()

        # It should create a diff
        self.assertEqual(TestModel.diffs.get_diffs(tm.id).count(), 2)

        tm.name = 'example'
        tm.save()

        # It should not create a diff
        self.assertEqual(TestModel.diffs.get_diffs(tm.id).count(), 2)

    def test_serialize_diff(self):
        """Asserts the serialize_diff method is called when available and the data is persisted."""

        def serialize_diff(self, dirty_fields):
            return {'test': 'data', 'fields': dirty_fields}

        tm = TestModel.objects.create(name='Example')
        # Add the method to the instance
        tm.serialize_diff = types.MethodType(serialize_diff, tm)

        tm.name = 'test'
        tm.save()

        # It should create a diff
        self.assertEqual(TestModel.diffs.get_diffs(tm.id).count(), 2)

        # It should have expected data
        expected = {'test': 'data', 'fields': ['name']}

        actual = TestModel.diffs.get_diffs(tm.id).last().diff

        self.assertEqual(expected, actual)

    def test_get_parent_object(self):
        """Asserts the get_parent_object method is called when available and data is persisted"""

        child, parent = self._get_family()

        child.name = 'child2'
        child.save()

        diff = TestModel.diffs.get_diffs(child.id).last()

        # It should have a parent
        self.assertEqual(diff.parent_object, parent)

    def test_get_diffs(self):
        """Asserts the related manager get_diffs returns only data for the given instance"""

        child, parent = self._get_family()

        self.assertEqual(TestModel.diffs.get_diffs(parent.id).count(), 1)

        parent_diff = TestModel.diffs.get_diffs(parent.id).last()
        self.assertIsNone(parent_diff.parent_object)

    def test_get_all_diffs(self):
        """Asserts the related manager get_all_diffs returns data for the given instance and
        when the instance is the parent.
        """

        child, parent = self._get_family()

        self.assertEqual(TestModel.diffs.get_all_diffs(parent.id).count(), 1)

        child.name = 'family'
        child.save()

        # it should include parent data
        self.assertEqual(TestModel.diffs.get_all_diffs(parent.id).count(), 2)

        last_diff = TestModel.diffs.get_all_diffs(parent.id).last()
        # it should be the parent
        self.assertEqual(parent, last_diff.parent_object)
