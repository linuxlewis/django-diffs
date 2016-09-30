from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from .compat import get_jsonfield_class
JSONField = get_jsonfield_class()


class DiffLogEntry(models.Model):
    """
    A model that represents a single diff for a given model.

    The actual model values are serialized to json and stored in
    `diff`.
    """
    content_type = models.ForeignKey(ContentType)
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now=True)
    created = models.BooleanField()
    diff = JSONField()
    object_id = models.PositiveIntegerField(db_index=True)
    parent_content_type = models.ForeignKey(ContentType, related_name='+', null=True)
    parent_object_id = models.PositiveIntegerField(db_index=True, null=True)
    parent_object = GenericForeignKey('parent_content_type', 'parent_object_id')


class DiffLogEntryQuerySet(models.QuerySet):
    """
    Queryset that always uses the DiffLogEntry model.
    """
    def __init__(self, *args, **kwargs):
        kwargs.update({'model': DiffLogEntry})
        super(DiffLogEntryQuerySet, self).__init__(*args, **kwargs)


class DiffLogEntryManager(models.Manager):
    """
    Manager to be set on registered models to access their diffs.

    @diffs.register
    class TestModel
        ...

    TestModel.diffs.get_all_diffs(pk)
    """

    def get_queryset(self):
        return DiffLogEntryQuerySet(using=self._db)

    def get_all_diffs(self, pk):
        """

        Returns all the diffs for the given pk inlcuding diffs where the pk is a parent.

        :param pk: Primary key of registered model instance
        :return: A queryset
        """
        return self.get_queryset().filter(Q(content_type=ContentType.objects.get_for_model(self.model),
                                            object_id=pk) |
                                          Q(parent_content_type=ContentType.objects.get_for_model(self.model),
                                            parent_object_id=pk))

    def get_diffs(self, pk):
        """
        Returns all the diffs for the given pk

        :param pk: Primary key of the registered model instance
        :return: A queryset
        """
        return self.get_queryset().filter(content_type=ContentType.objects.get_for_model(self.model),
                                          object_id=pk)

