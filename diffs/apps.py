from django.apps import AppConfig

from diffs import klasses_to_connect, signals

class DiffLogConfig(AppConfig):
    name = 'diffs'
    verbose_name = 'Diffs'

    def ready(self):
        for klass in klasses_to_connect:
            signals.connect(klass)

