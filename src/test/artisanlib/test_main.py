import threading

from PyQt5.QtWidgets import QApplication, QMessageBox

from artisanlib.main import Artisan, app, ApplicationWindow

from test import plugins


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


class ApplicationWindowTest(plugins.ArtisanTestCase):
    """
    Verify ApplicationWindowTest behaviours.
    """

    def test_artisanviewer_first_start_message_box(self):
        """
        A message box is displayed on when artisanviewer_first_start parameter
        is passed.
        """

        result_object = {
            "exception": None,
        }

        arguments = {
            'locale': 'en',
            'artisanviewer_first_start': True,
        }

        def thread_target(results, aw_kwargs):
            try:
                ApplicationWindow(**aw_kwargs)
            except Exception as exc:
                results["exception"] = exc

        t = threading.Thread(target=thread_target, args=(result_object, arguments))
        t.start()

        while (
                QApplication.activeModalWidget() is None
                and result_object["exception"] is None
        ):
            pass

        if result_object["exception"]:
            raise result_object["exception"]

        msg_box = QApplication.activeModalWidget()
        self.assertIsInstance(msg_box, QMessageBox)

        msg_box.done(1)

        t.join()
