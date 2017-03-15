from __future__ import absolute_import, unicode_literals
import logging

from django.core import serializers
from django.db import connection
from django.db.models.signals import pre_save, post_save

from .helpers import precise_timestamp

from .settings import diffs_settings

logger = logging.getLogger("diffs")


def on_pre_save(sender, instance, **kwargs):
    instance.__dirty_fields = instance.get_dirty_fields()


def on_post_save(sender, instance, created, **kwargs):
    if instance.__dirty_fields or created:
        # check if we should send it
        if hasattr(instance, 'send_diff') and instance.send_diff() is False:
            logger.debug("Skipped diff because send_diff returned False")
            return

        # get the data
        if hasattr(instance, 'serialize_diff'):
            data = instance.serialize_diff(instance.__dirty_fields, created=created)
        else:
            data = serialize_object(instance, instance.__dirty_fields)

        if data:
            model = instance
            # check if should be related to another "parent" model
            if hasattr(instance, 'get_diff_parent'):
                parent = instance.get_diff_parent()
                if parent:
                    model = parent
            create_kwargs = {
                'data': data,
                'created': created,
                'pk': model.id,
                'model_cls': model.__class__,
                'timestamp': getattr(instance, '_last_save_at', precise_timestamp())
            }
            # Respect the transaction if we can and should.
            if hasattr(connection, 'on_commit') and diffs_settings['use_transactions']:
                connection.on_commit(lambda: sender.diffs.create(**create_kwargs))
            else:
                sender.diffs.create(**create_kwargs)
        else:
            logger.debug("Skipped diff because it was emtpy.")
        # clean up
        del instance.__dirty_fields
    else:
        logger.debug("Skipped diff because no fields had changed.")


def serialize_object(instance, dirty_fields):
    """Serializes a django model using the default serialization."""
    return serializers.serialize('json', [instance], fields=list(dirty_fields.keys()))


def connect(cls):
    pre_save.connect(on_pre_save, cls)
    post_save.connect(on_post_save, cls)
