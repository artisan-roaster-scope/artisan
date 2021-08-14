from contextlib import contextmanager
import unittest


class ArtisanTestCase(unittest.TestCase):
    @contextmanager
    def assertNothingRaised(self, exception_klass=Exception):
        try:
            yield
        except Exception as e:
            if isinstance(e, exception_klass):
                self.fail('Exception %s was raised' % e.__repr__())
