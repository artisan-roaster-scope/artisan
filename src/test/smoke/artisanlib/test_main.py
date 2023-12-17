from artisanlib.main import Artisan, app

class TestArtisan:
    def test_instantiation(self) -> None:
        assert isinstance(app, Artisan)
