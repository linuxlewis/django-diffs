from __future__ import absolute_import, unicode_literals

__version__ = '0.1.16'
default_app_config = 'diffs.apps.DiffLogConfig'

klasses_to_connect = []


def register(cls):
    """
    Decorator function that registers a class to record diffs.

    @diffs.register
    class ExampleModel(models.Model):
        ...
    """
    from django.apps import apps as django_apps
    from dirtyfields import DirtyFieldsMixin

    from .models import DiffModelManager, DiffModelDescriptor
    from .signals import connect
    # check if class implemented get_dirty_fields else hack in dirtyfields
    if not hasattr(cls, 'get_dirty_fields') and DirtyFieldsMixin not in cls.__bases__:
        cls.__bases__ = (DirtyFieldsMixin,) + cls.__bases__

    setattr(cls, 'diffs', DiffModelDescriptor(DiffModelManager(cls)))

    if not django_apps.ready:
        klasses_to_connect.append(cls)
    else:
        connect(cls)

    return cls


def get_connection():
    """Helper method to get redis connection configured by settings"""
    import redis
    import fakeredis
    from .settings import diffs_settings

    if not diffs_settings['test_mode']:
        return redis.Redis(**diffs_settings['redis'])
    else:
        return fakeredis.FakeRedis()
