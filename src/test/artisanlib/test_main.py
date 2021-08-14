# from test.plugins import ArtisanTestCase
import unittest
from test import plugins

from artisanlib.main import Artisan, app


class ArtisanTest(plugins.ArtisanTestCase):
    def test_instantiation(self):
        # Would like to change to
        #
        # with self.assertNothingRaised:
        #     Artisan([])
        #
        # However this results in segmentation fault right at
        # the moment. Probably because you have 2 instances of the
        # QT app running at the same time.
        self.assertIsInstance(app, Artisan)
