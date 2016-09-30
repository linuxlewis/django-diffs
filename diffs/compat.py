import django
from django.core.exceptions import ImproperlyConfigured


def get_jsonfield_class():
    if django.VERSION < (1, 9):
        try:
            from jsonfield import JSONField
        except ImportError:
            raise ImproperlyConfigured("diffs requires JSONField for Django versions < 1.9. Please pip install jsonfield.")
    else:
        from django.contrib.postgres.fields import JSONField
    return JSONField
