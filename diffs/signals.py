from __future__ import absolute_import, unicode_literals
from django.core import serializers
from django.db.models.signals import pre_save, post_save


def on_pre_save(sender, instance, **kwargs):
    instance.__dirty_fields = list(instance.get_dirty_fields().keys())


def on_post_save(sender, instance, created, **kwargs):
    from django.contrib.contenttypes.models import ContentType
    from .models import DiffLogEntry

    if instance.__dirty_fields:
        # get the data
        if hasattr(instance, 'serialize_diff'):
            data = instance.serialize_diff(instance.__dirty_fields)
        else:
            data = serialize_object(instance, instance.__dirty_fields)

        create_kwargs = {
            'content_type': ContentType.objects.get_for_model(sender),
            'created': created,
            'diff': data,
            'object_id': instance.id,
        }

        # get parent
        parent = None
        if hasattr(instance, 'get_parent_object'):
            parent = instance.get_parent_object()

        if parent:
            create_kwargs.update({
                'parent_content_type': ContentType.objects.get_for_model(type(parent)),
                'parent_object_id': parent.id
            })

        DiffLogEntry.objects.create(**create_kwargs)

        del instance.__dirty_fields


def serialize_object(instance, dirty_fields):
    """Serializes a django model using the default serialization."""
    return serializers.serialize('json', [instance], fields=dirty_fields)


def connect(klass):
    pre_save.connect(on_pre_save, klass)
    post_save.connect(on_post_save, klass)
