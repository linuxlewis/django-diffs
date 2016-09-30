from __future__ import absolute_import, unicode_literals

__version__ = '0.0.1'
default_app_config = 'diffs.apps.DiffLogConfig'

klasses_to_connect = []


def register(klass):
    """
    Decorator function that registers a class to record diffs.

    @register
    class ExampleModel(models.Model):
        ...
    """
    from django.apps import apps as django_apps
    from dirtyfields import DirtyFieldsMixin

    from .models import DiffLogEntryManager
    from .signals import connect
    # Hack to add dirtyfieldsmixin automatically
    if DirtyFieldsMixin not in klass.__bases__:
        klass.__bases__ = (DirtyFieldsMixin,) + klass.__bases__

    klass.add_to_class('diffs', DiffLogEntryManager())

    if not django_apps.ready:
        klasses_to_connect.append(klass)
    else:
        connect(klass)

    return klass
