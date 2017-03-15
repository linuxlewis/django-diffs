from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from redis.exceptions import ResponseError

import diffs
from diffs.settings import diffs_settings
from diffs.helpers import precise_timestamp


class Command(BaseCommand):
    help = 'SCANs the redis database and removes old SortedSet elements'

    def handle(self, *args, **options):

        db = diffs.get_connection()

        dt = timezone.now() - timedelta(seconds=diffs_settings['max_element_age'])

        min_age = precise_timestamp(dt=dt)

        self.stdout.write('Minimum age: {}'.format(min_age))

        for key in db.scan_iter():
            key_str = key.decode("utf-8")
            if key_str.startswith(diffs_settings['prefix']):
                try:
                    ret = db.zremrangebyscore(key, 0, min_age)
                    self.stdout.write('{} elements removed from {}'.format(ret, key_str))
                except ResponseError as err:
                    self.stderr.write(self.style.NOTICE('Pruning key "{}" failed: "{}"'.format(key_str, err)))
            else:
                self.stdout.write("skipping key: {}".format(key_str))
