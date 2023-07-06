from artisanlib.main import Artisan, app

class TestArtisan:
    def test_instantiation(self):
        assert isinstance(app, Artisan)
