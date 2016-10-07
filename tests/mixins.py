from diffs.settings import diffs_settings

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


class TestModeMixin(object):

    @classmethod
    def setUpClass(cls):
        cls.p = patch.dict(diffs_settings, test_mode=True)
        cls.p.start()
        super(TestModeMixin, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.p.stop()
        super(TestModeMixin, cls).tearDownClass()