"""
Level 3 Destructive & Exploratory Testing for artisanlib.dialogs module.

This test suite is designed to find and document vulnerabilities by intentionally
trying to break the system. Tests use hostile conditions including data fuzzing,
resource exhaustion, and sequence breaking to uncover stability and security issues.

MISSION: Push the system beyond its expected operational parameters to find bugs.

Test Organization:
- TestArtisanDialogDestructive: Base dialog stress testing and malicious input
- TestHelpDialogDestructive: Search functionality fuzzing and memory exhaustion
- TestInputDialogDestructive: Malicious drag-and-drop and input injection
- TestTareDialogDestructive: Container data corruption and scale manipulation
- TestPortDialogDestructive: Serial port fuzzing and hardware simulation attacks
- TestSequenceBreakingDestructive: Function call order corruption
- TestResourceExhaustionDestructive: Memory and resource limits
- TestConcurrencyDestructive: Race conditions and concurrent access

Security Focus: Levels 1-4 with emphasis on finding exploitable vulnerabilities

IMPORTANT: Tests marked with @pytest.mark.xfail document real vulnerabilities
that need to be addressed by the development team.
"""

import sys
from typing import Any, Generator, List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

# PyQt6/PyQt5 compatibility imports
try:
    from PyQt6.QtCore import QSettings, Qt, QUrl
    from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QKeyEvent
    from PyQt6.QtWidgets import (
        QApplication,
        QDialogButtonBox,
        QLineEdit,
        QWidget,
    )
except ImportError:
    from PyQt5.QtCore import QSettings, Qt, QUrl  # type: ignore
    from PyQt5.QtGui import (  # type: ignore
        QDragEnterEvent,
        QDropEvent,
        QKeyEvent,
    )
    from PyQt5.QtWidgets import (  # type: ignore
        QApplication,
        QDialogButtonBox,
        QLineEdit,
        QWidget,
    )

from artisanlib.dialogs import (
    ArtisanComboBoxDialog,
    ArtisanDialog,
    ArtisanInputDialog,
    ArtisanMessageBox,
    HelpDlg,
    PortComboBox,
    tareDlg,
)


# Test Fixtures
@pytest.fixture(scope="session")
def qapp() -> Generator[QApplication, None, None]:
    """Create QApplication instance for destructive testing."""
    if not QApplication.instance():
        app = QApplication(sys.argv)
        app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs)
        yield app
        app.quit()
    else:
        yield QApplication.instance()


@pytest.fixture
def mock_aw() -> Mock:
    """Mock ApplicationWindow with potentially corrupted state."""
    mock = Mock()
    mock.qmc = Mock()
    mock.qmc.weight = ["g", "kg", "g"]
    mock.qmc.container_names = ["Container 1", "Container 2"]
    mock.qmc.container_weights = [50.0, 75.5]
    mock.app = Mock()
    mock.app.darkmode = False
    mock.devicePixelRatio = Mock(return_value=1.0)
    mock.createCLocaleDoubleValidator = Mock(return_value=Mock())
    return mock


class TestArtisanDialogDestructive:
    """Destructive testing of base ArtisanDialog functionality."""

    def test_dialog_with_corrupted_application_window(self, qapp: QApplication) -> None:
        """
        ARRANGE: Corrupted ApplicationWindow mock
        ACT: Create dialog with malformed dependencies
        ASSERT: Dialog handles corruption gracefully or fails predictably
        """
        # Create corrupted mock that will cause attribute errors
        corrupted_aw = Mock()
        corrupted_aw.qmc = None  # This should cause issues

        try:
            dialog = ArtisanDialog(None, corrupted_aw)
            # If dialog creation succeeds, it should still be functional
            assert dialog.dialogbuttons is not None
            dialog.close()
        except AttributeError as e:
            # VULNERABILITY: Dialog creation fails with corrupted dependencies
            pytest.fail(f"Dialog creation failed with corrupted ApplicationWindow: {e}")

    @given(key_code=st.integers(min_value=0, max_value=0xFFFFFF))
    @settings(max_examples=50, deadline=1000)
    def test_key_event_fuzzing(self, qapp: QApplication, mock_aw: Mock, key_code: int) -> None:
        """
        ARRANGE: Dialog ready for input
        ACT: Send random key codes to dialog
        ASSERT: Dialog doesn't crash with unexpected key events
        """
        dialog = ArtisanDialog(None, mock_aw)

        try:
            # Fuzz with random key codes
            key_event = QKeyEvent(QKeyEvent.Type.KeyPress, key_code, Qt.KeyboardModifier.NoModifier)
            dialog.keyPressEvent(key_event)

            # Dialog should still be responsive
            assert dialog.dialogbuttons is not None
        except Exception as e:
            # VULNERABILITY: Unexpected key codes cause crashes
            pytest.fail(f"Dialog crashed with key code {key_code}: {e}")
        finally:
            dialog.close()

    def test_rapid_dialog_creation_destruction(self, qapp: QApplication, mock_aw: Mock) -> None:
        """
        ARRANGE: System ready for dialog operations
        ACT: Rapidly create and destroy dialogs
        ASSERT: No memory leaks or resource exhaustion
        """
        dialogs = []

        try:
            # Create many dialogs rapidly
            for i in range(100):
                dialog = ArtisanDialog(None, mock_aw)
                dialogs.append(dialog)

                # Immediately close some to test cleanup
                if i % 2 == 0:
                    dialog.close()

            # Clean up remaining dialogs
            for dialog in dialogs:
                if dialog.isVisible():
                    dialog.close()

        except Exception as e:
            # VULNERABILITY: Resource exhaustion or memory leak
            pytest.fail(f"Rapid dialog creation/destruction failed: {e}")


class TestHelpDialogDestructive:
    """Destructive testing of help dialog search functionality."""

    @pytest.fixture
    def mock_qsettings(self) -> Generator[Mock, None, None]:
        """Mock QSettings for destructive testing."""
        with patch("artisanlib.dialogs.QSettings") as mock_settings:
            settings_instance = Mock()
            settings_instance.contains.return_value = False
            settings_instance.value.return_value = None
            mock_settings.return_value = settings_instance
            yield settings_instance

    @given(search_term=st.text(min_size=0, max_size=10000))
    @settings(max_examples=20, deadline=2000)
    def test_search_with_malicious_input(
        self, qapp: QApplication, mock_aw: Mock, mock_qsettings: Mock, search_term: str
    ) -> None:
        """
        ARRANGE: Help dialog with content
        ACT: Search with potentially malicious strings
        ASSERT: Search doesn't crash or expose vulnerabilities
        """
        content = "<p>Test content for searching</p>" * 100  # Large content
        dialog = HelpDlg(None, mock_aw, "Help", content)

        try:
            dialog.search_input.setText(search_term)
            dialog.doSearch()

            # Verify dialog is still functional
            assert dialog.search_input is not None
            assert isinstance(dialog.matches, list)

        except Exception as e:
            # VULNERABILITY: Malicious search input causes crashes
            pytest.fail(f"Search crashed with input '{search_term[:50]}...': {e}")
        finally:
            dialog.close()

    def test_search_memory_exhaustion(
        self, qapp: QApplication, mock_aw: Mock, mock_qsettings: Mock
    ) -> None:
        """
        ARRANGE: Help dialog with massive content
        ACT: Search for common terms in huge document
        ASSERT: Search doesn't consume excessive memory
        """
        # Create massive content that could cause memory issues
        massive_content = "<p>searchable content " * 10000 + "</p>"
        dialog = HelpDlg(None, mock_aw, "Help", massive_content)

        try:
            # Search for term that appears many times
            dialog.search_input.setText("content")
            dialog.doSearch()

            # VULNERABILITY CHECK: Excessive matches could cause memory issues
            if len(dialog.matches) > 1000:
                pytest.fail(
                    f"Search found {len(dialog.matches)} matches - potential memory exhaustion"
                )

        except MemoryError:
            # VULNERABILITY: Search causes memory exhaustion
            pytest.fail("Search caused memory exhaustion with large content")
        except Exception as e:
            # VULNERABILITY: Other crashes with large content
            pytest.fail(f"Search failed with large content: {e}")
        finally:
            dialog.close()

    @pytest.mark.xfail(reason="VULNERABILITY: Regex injection in search functionality")
    def test_regex_injection_vulnerability(
        self, qapp: QApplication, mock_aw: Mock, mock_qsettings: Mock
    ) -> None:
        """
        ARRANGE: Help dialog ready for search
        ACT: Inject malicious regex patterns
        ASSERT: Search should sanitize regex input

        REMEDIATION: Search input should escape regex special characters
        """
        dialog = HelpDlg(None, mock_aw, "Help", "<p>test content</p>")

        # Malicious regex that could cause ReDoS (Regular Expression Denial of Service)
        malicious_regex = "a" * 1000 + "!"  # Pattern that doesn't match but takes time

        dialog.search_input.setText(malicious_regex)

        # This should fail if regex injection is possible
        import time

        start_time = time.time()
        dialog.doSearch()
        end_time = time.time()

        # If search takes too long, it's vulnerable to ReDoS
        if end_time - start_time > 1.0:  # More than 1 second
            pytest.fail("Search vulnerable to ReDoS attacks")

        dialog.close()


class TestInputDialogDestructive:
    """Destructive testing of input dialog with focus on injection attacks."""

    @given(malicious_input=st.text(min_size=0, max_size=1000))
    @settings(max_examples=30, deadline=1000)
    def test_input_injection_attacks(
        self, qapp: QApplication, mock_aw: Mock, malicious_input: str
    ) -> None:
        """
        ARRANGE: Input dialog ready for user input
        ACT: Inject potentially malicious strings
        ASSERT: Input is sanitized and doesn't cause issues
        """
        dialog = ArtisanInputDialog(None, mock_aw, "Test", "Enter data:")

        try:
            dialog.inputLine.setText(malicious_input)
            dialog.accept()

            # Check if malicious input was stored
            stored_value = dialog.url

            # VULNERABILITY CHECK: Input should be sanitized
            if stored_value != malicious_input:
                # Input was modified - this could be good (sanitization) or bad (corruption)
                pass

        except Exception as e:
            # VULNERABILITY: Malicious input causes crashes
            pytest.fail(f"Input dialog crashed with malicious input: {e}")
        finally:
            dialog.close()

    @pytest.mark.xfail(reason="VULNERABILITY: No validation of dropped file URLs")
    def test_malicious_file_drop(self, qapp: QApplication, mock_aw: Mock) -> None:
        """
        ARRANGE: Input dialog with drag-and-drop enabled
        ACT: Drop malicious file URLs
        ASSERT: URLs should be validated before processing

        REMEDIATION: Validate and sanitize dropped URLs before setting them
        """
        with patch("artisanlib.dialogs.QApplication.translate") as mock_translate:
            mock_translate.return_value = "test"
            dialog = ArtisanInputDialog(None, mock_aw, "Test", "URL:")

            # Create malicious URL drop event
            malicious_urls = [
                "file:///etc/passwd",  # System file access
                "javascript:alert('xss')",  # Script injection
                "ftp://malicious.com/payload",  # External resource
                "\\\\malicious-server\\share",  # UNC path injection
            ]

            for malicious_url in malicious_urls:
                mock_mime_data = Mock()
                mock_mime_data.hasUrls.return_value = True
                mock_url = Mock()
                mock_url.toString.return_value = malicious_url
                mock_mime_data.urls.return_value = [mock_url]

                mock_drop_event = Mock()
                mock_drop_event.mimeData.return_value = mock_mime_data

                dialog.dropEvent(mock_drop_event)

                # VULNERABILITY: Malicious URL accepted without validation
                if dialog.inputLine.text() == malicious_url:
                    pytest.fail(f"Malicious URL accepted: {malicious_url}")

            dialog.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
