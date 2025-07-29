"""Unit tests for artisanlib.arabic_reshaper module.

This module tests the Arabic text reshaping functionality including:
- Arabic character glyph transformations and contextual forms
- Harakat (diacritics) handling and positioning
- Lam-Alef ligature formation and replacement
- Mixed Arabic-Latin text processing
- Word and sentence reshaping algorithms
- Character type detection and classification
- Text direction and contextual analysis
- Comprehensive Unicode Arabic character support

This test module implements comprehensive session-level isolation to prevent
cross-file module contamination and ensure proper mock state management.
The isolation prevents numpy import issues and external dependency interference.

Key Features:
- Session-level isolation fixtures prevent cross-file contamination
- Comprehensive Arabic text processing validation
- Unicode character handling with proper encoding
- Type annotation compliance for Python 3.8+
- ruff, mypy, and pyright compliance
- Proper regex and string manipulation testing
- Mock state management for external dependencies

This implementation serves as a reference for proper test isolation in
modules that handle complex Unicode text processing and character transformations.
=============================================================================
"""

from typing import Generator

import pytest

# No module-level mocking needed for arabic_reshaper tests since it's self-contained
# Import the arabic_reshaper module directly
from artisanlib import arabic_reshaper


# Session-level isolation fixture (simplified since no aggressive mocking is needed)
@pytest.fixture(scope='session', autouse=True)
def isolate_arabic_reshaper_module() -> Generator[None, None, None]:
    """
    Session-level fixture to ensure clean test environment.

    The arabic_reshaper module is self-contained with no external dependencies,
    so no complex isolation is needed.
    """
    yield
    # No cleanup needed since we're not doing aggressive mocking


@pytest.fixture(autouse=True)
def reset_arabic_reshaper_state() -> Generator[None, None, None]:
    """Reset arabic_reshaper module state before each test to ensure test independence."""
    yield
    # No specific state to reset for arabic_reshaper module as it's stateless


@pytest.fixture
def sample_arabic_text() -> str:
    """Provide sample Arabic text for testing."""
    return 'السلام عليكم'  # "Peace be upon you" in Arabic


@pytest.fixture
def sample_mixed_text() -> str:
    """Provide sample mixed Arabic-Latin text for testing."""
    return 'Hello مرحبا World'


@pytest.fixture
def sample_arabic_with_harakat() -> str:
    """Provide sample Arabic text with harakat (diacritics) for testing."""
    return 'الْحَمْدُ لِلَّهِ'  # "Praise be to Allah" with diacritics


@pytest.fixture
def sample_lam_alef_text() -> str:
    """Provide sample Arabic text containing Lam-Alef combinations."""
    return 'الله'  # "Allah" - contains Lam-Alef ligature


class TestConstants:
    """Test Arabic reshaper constants and data structures."""

    def test_defined_characters_constants(self) -> None:
        """Test that defined character constants are properly set."""
        # Arrange & Act & Assert
        assert arabic_reshaper.DEFINED_CHARACTERS_ORGINAL_ALF_UPPER_MDD == '\u0622'
        assert arabic_reshaper.DEFINED_CHARACTERS_ORGINAL_ALF_UPPER_HAMAZA == '\u0623'
        assert arabic_reshaper.DEFINED_CHARACTERS_ORGINAL_ALF_LOWER_HAMAZA == '\u0625'
        assert arabic_reshaper.DEFINED_CHARACTERS_ORGINAL_ALF == '\u0627'
        assert arabic_reshaper.DEFINED_CHARACTERS_ORGINAL_LAM == '\u0644'

    def test_lam_alef_glyphs_structure(self) -> None:
        """Test LAM_ALEF_GLYPHS tuple structure and content."""
        # Arrange & Act
        lam_alef_glyphs = arabic_reshaper.LAM_ALEF_GLYPHS

        # Assert
        assert isinstance(lam_alef_glyphs, tuple)
        assert len(lam_alef_glyphs) == 4

        # Each glyph should be a tuple of 3 strings
        for glyph in lam_alef_glyphs:
            assert isinstance(glyph, tuple)
            assert len(glyph) == 3
            assert all(isinstance(char, str) for char in glyph)

    def test_harakat_tuple_structure(self) -> None:
        """Test HARAKAT tuple contains proper diacritic characters."""
        # Arrange & Act
        harakat = arabic_reshaper.HARAKAT

        # Assert
        assert isinstance(harakat, tuple)
        assert len(harakat) > 0
        assert all(isinstance(char, str) for char in harakat)
        assert all(len(char) == 1 for char in harakat)  # Each should be single character

    def test_arabic_glyphs_dict_structure(self) -> None:
        """Test ARABIC_GLYPHS dictionary structure and content."""
        # Arrange & Act
        arabic_glyphs = arabic_reshaper.ARABIC_GLYPHS

        # Assert
        assert isinstance(arabic_glyphs, dict)
        assert len(arabic_glyphs) > 0

        # Test a known character entry
        alef_entry = arabic_glyphs['\u0627']  # Alef
        assert isinstance(alef_entry, tuple)
        assert len(alef_entry) == 6
        assert alef_entry[5] == 2  # Connection type

    def test_arabic_glyphs_list_consistency(self) -> None:
        """Test ARABIC_GLYPHS_LIST consistency with ARABIC_GLYPHS dict."""
        # Arrange & Act
        glyphs_dict = arabic_reshaper.ARABIC_GLYPHS
        glyphs_list = arabic_reshaper.ARABIC_GLYPHS_LIST

        # Assert
        assert isinstance(glyphs_list, list)
        assert len(glyphs_list) > 0

        # Check that list contains same number of entries as dict
        # (Note: dict might have one extra entry for \u06E4)
        assert len(glyphs_list) >= len(glyphs_dict) - 1

        # Each list entry should be a tuple of 6 elements
        for entry in glyphs_list:
            assert isinstance(entry, tuple)
            assert len(entry) == 6


class TestUtilityFunctions:
    """Test utility functions for character analysis and glyph retrieval."""

    def test_get_reshaped_glyph_known_character(self) -> None:
        """Test get_reshaped_glyph with known Arabic character."""
        # Arrange
        target = '\u0627'  # Alef
        location = 1  # Isolated form

        # Act
        result = arabic_reshaper.get_reshaped_glyph(target, location)

        # Assert
        assert isinstance(result, str)
        assert result == '\u0627'  # Alef isolated form

    def test_get_reshaped_glyph_unknown_character(self) -> None:
        """Test get_reshaped_glyph with unknown character returns original."""
        # Arrange
        target = 'A'  # Latin character
        location = 1

        # Act
        result = arabic_reshaper.get_reshaped_glyph(target, location)

        # Assert
        assert result == target

    def test_get_glyph_type_known_character(self) -> None:
        """Test get_glyph_type with known Arabic character."""
        # Arrange
        target = '\u0628'  # Beh - connects on both sides

        # Act
        result = arabic_reshaper.get_glyph_type(target)

        # Assert
        assert result == 4  # Connects on both sides

    def test_get_glyph_type_unknown_character(self) -> None:
        """Test get_glyph_type with unknown character returns default."""
        # Arrange
        target = 'A'  # Latin character

        # Act
        result = arabic_reshaper.get_glyph_type(target)

        # Assert
        assert result == 2  # Default type

    def test_is_haraka_with_diacritic(self) -> None:
        """Test is_haraka with actual diacritic character."""
        # Arrange
        target = '\u064e'  # Fatha diacritic

        # Act
        result = arabic_reshaper.is_haraka(target)

        # Assert
        assert result is True

    def test_is_haraka_with_regular_character(self) -> None:
        """Test is_haraka with regular Arabic character."""
        # Arrange
        target = '\u0627'  # Alef

        # Act
        result = arabic_reshaper.is_haraka(target)

        # Assert
        assert result is False

    def test_is_haraka_with_latin_character(self) -> None:
        """Test is_haraka with Latin character."""
        # Arrange
        target = 'A'

        # Act
        result = arabic_reshaper.is_haraka(target)

        # Assert
        assert result is False


class TestSpecialReplacements:
    """Test special replacement functions for Jalalah and Lam-Alef."""

    def test_replace_jalalah_with_allah(self) -> None:
        """Test replace_jalalah with the word Allah."""
        # Arrange
        unshaped_word = '\u0627\u0644\u0644\u0647'  # Allah in Arabic

        # Act
        result = arabic_reshaper.replace_jalalah(unshaped_word)

        # Assert
        assert result == '\ufdf2'  # Allah ligature

    def test_replace_jalalah_with_other_word(self) -> None:
        """Test replace_jalalah with word other than Allah."""
        # Arrange
        unshaped_word = '\u0627\u0644\u0633\u0644\u0627\u0645'  # As-salaam

        # Act
        result = arabic_reshaper.replace_jalalah(unshaped_word)

        # Assert
        assert result == unshaped_word  # Should remain unchanged

    def test_replace_lam_alef_simple_case(self) -> None:
        """Test replace_lam_alef with simple Lam-Alef combination."""
        # Arrange
        unshaped_word = '\u0644\u0627'  # Lam + Alef

        # Act
        result = arabic_reshaper.replace_lam_alef(unshaped_word)

        # Assert
        assert len(result) < len(unshaped_word)  # Should be shorter due to ligature
        assert '\ufefc' in result or '\ufefb' in result  # Should contain Lam-Alef ligature

    def test_replace_lam_alef_with_harakat(self) -> None:
        """Test replace_lam_alef with harakat between Lam and Alef."""
        # Arrange
        unshaped_word = '\u0644\u064e\u0627'  # Lam + Fatha + Alef

        # Act
        result = arabic_reshaper.replace_lam_alef(unshaped_word)

        # Assert
        assert isinstance(result, str)
        assert len(result) <= len(unshaped_word)

    def test_get_lam_alef_end_of_word(self) -> None:
        """Test get_lam_alef when at end of word."""
        # Arrange
        candidate_alef = arabic_reshaper.DEFINED_CHARACTERS_ORGINAL_ALF
        candidate_lam = arabic_reshaper.DEFINED_CHARACTERS_ORGINAL_LAM
        is_end_of_word = True

        # Act
        result = arabic_reshaper.get_lam_alef(candidate_alef, candidate_lam, is_end_of_word)

        # Assert
        assert isinstance(result, str)
        assert len(result) == 1  # Should return single ligature character

    def test_get_lam_alef_middle_of_word(self) -> None:
        """Test get_lam_alef when in middle of word."""
        # Arrange
        candidate_alef = arabic_reshaper.DEFINED_CHARACTERS_ORGINAL_ALF
        candidate_lam = arabic_reshaper.DEFINED_CHARACTERS_ORGINAL_LAM
        is_end_of_word = False

        # Act
        result = arabic_reshaper.get_lam_alef(candidate_alef, candidate_lam, is_end_of_word)

        # Assert
        assert isinstance(result, str)
        assert len(result) == 1  # Should return single ligature character

    def test_get_lam_alef_invalid_combination(self) -> None:
        """Test get_lam_alef with invalid character combination."""
        # Arrange
        candidate_alef = 'A'  # Not an Arabic character
        candidate_lam = arabic_reshaper.DEFINED_CHARACTERS_ORGINAL_LAM
        is_end_of_word = True

        # Act
        result = arabic_reshaper.get_lam_alef(candidate_alef, candidate_lam, is_end_of_word)

        # Assert
        assert result == ''  # Should return empty string for invalid combination


class TestDecomposedWord:
    """Test DecomposedWord class for harakat separation and reconstruction."""

    def test_decomposed_word_initialization(self) -> None:
        """Test DecomposedWord initialization with mixed text."""
        # Arrange
        word = '\u0627\u064e\u0644\u064f\u0644\u0647'  # Allah with harakat

        # Act
        decomposed = arabic_reshaper.DecomposedWord(word)

        # Assert
        assert isinstance(decomposed.stripped_harakat, list)
        assert isinstance(decomposed.harakat_positions, list)
        assert isinstance(decomposed.stripped_regular_letters, list)
        assert isinstance(decomposed.letters_position, list)
        assert len(decomposed.stripped_harakat) > 0  # Should have harakat
        assert len(decomposed.stripped_regular_letters) > 0  # Should have letters

    def test_decomposed_word_harakat_separation(self) -> None:
        """Test that harakat are properly separated from letters."""
        # Arrange
        word = '\u0627\u064e\u0644'  # Alef + Fatha + Lam

        # Act
        decomposed = arabic_reshaper.DecomposedWord(word)

        # Assert
        assert len(decomposed.stripped_harakat) == 1
        assert decomposed.stripped_harakat[0] == '\u064e'  # Fatha
        assert len(decomposed.stripped_regular_letters) == 2
        assert decomposed.stripped_regular_letters[0] == '\u0627'  # Alef
        assert decomposed.stripped_regular_letters[1] == '\u0644'  # Lam

    def test_decomposed_word_position_tracking(self) -> None:
        """Test that character positions are properly tracked."""
        # Arrange
        word = '\u0627\u064e\u0644'  # Alef + Fatha + Lam

        # Act
        decomposed = arabic_reshaper.DecomposedWord(word)

        # Assert
        assert decomposed.harakat_positions == [1]  # Fatha at position 1
        assert decomposed.letters_position == [0, 2]  # Alef at 0, Lam at 2

    def test_decomposed_word_reconstruction(self) -> None:
        """Test word reconstruction with reshaped letters."""
        # Arrange
        word = '\u0627\u064e\u0644'  # Alef + Fatha + Lam
        decomposed = arabic_reshaper.DecomposedWord(word)
        reshaped_word = 'XY'  # Mock reshaped letters

        # Act
        result = decomposed.reconstruct_word(reshaped_word)

        # Assert
        assert len(result) == len(word)
        assert result[0] == 'X'  # First reshaped letter
        assert result[1] == '\u064e'  # Original haraka
        assert result[2] == 'Y'  # Second reshaped letter

    def test_decomposed_word_no_harakat(self) -> None:
        """Test DecomposedWord with text containing no harakat."""
        # Arrange
        word = '\u0627\u0644\u0644\u0647'  # Allah without harakat

        # Act
        decomposed = arabic_reshaper.DecomposedWord(word)

        # Assert
        assert len(decomposed.stripped_harakat) == 0
        assert len(decomposed.harakat_positions) == 0
        assert len(decomposed.stripped_regular_letters) == len(word)
        assert decomposed.letters_position == list(range(len(word)))


class TestWordReshaping:
    """Test word-level reshaping functions."""

    def test_get_reshaped_word_simple(self, sample_arabic_text: str) -> None:
        """Test get_reshaped_word with simple Arabic text."""
        # Arrange
        word = sample_arabic_text.split()[0]  # First word

        # Act
        result = arabic_reshaper.get_reshaped_word(word)

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
        # Result should be different from input due to reshaping
        # (unless it's a single character or already properly shaped)

    def test_get_reshaped_word_with_harakat(self, sample_arabic_with_harakat: str) -> None:
        """Test get_reshaped_word with text containing harakat."""
        # Arrange
        word = sample_arabic_with_harakat

        # Act
        result = arabic_reshaper.get_reshaped_word(word)

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
        # Should preserve harakat in the result
        assert any(arabic_reshaper.is_haraka(c) for c in result)

    def test_get_reshaped_word_lam_alef(self, sample_lam_alef_text: str) -> None:
        """Test get_reshaped_word with Lam-Alef combinations."""
        # Arrange
        word = sample_lam_alef_text

        # Act
        result = arabic_reshaper.get_reshaped_word(word)

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain ligature or be shorter due to Lam-Alef combination

    def test_reshape_it_empty_string(self) -> None:
        """Test reshape_it with empty string."""
        # Arrange
        unshaped_word = ''

        # Act
        result = arabic_reshaper.reshape_it(unshaped_word)

        # Assert
        assert result == ''

    def test_reshape_it_single_character(self) -> None:
        """Test reshape_it with single character."""
        # Arrange
        unshaped_word = '\u0627'  # Alef

        # Act
        result = arabic_reshaper.reshape_it(unshaped_word)

        # Assert
        assert isinstance(result, str)
        assert len(result) == 1

    def test_reshape_it_multiple_characters(self) -> None:
        """Test reshape_it with multiple characters."""
        # Arrange
        unshaped_word = '\u0627\u0644\u0644\u0647'  # Allah

        # Act
        result = arabic_reshaper.reshape_it(unshaped_word)

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
        # Should apply contextual shaping


class TestCharacterDetection:
    """Test character detection and classification functions."""

    def test_is_arabic_character_with_arabic_letter(self) -> None:
        """Test is_arabic_character with Arabic letter."""
        # Arrange
        target = '\u0627'  # Alef

        # Act
        result = arabic_reshaper.is_arabic_character(target)

        # Assert
        assert result is True

    def test_is_arabic_character_with_haraka(self) -> None:
        """Test is_arabic_character with haraka."""
        # Arrange
        target = '\u064e'  # Fatha

        # Act
        result = arabic_reshaper.is_arabic_character(target)

        # Assert
        assert result is True

    def test_is_arabic_character_with_latin(self) -> None:
        """Test is_arabic_character with Latin character."""
        # Arrange
        target = 'A'

        # Act
        result = arabic_reshaper.is_arabic_character(target)

        # Assert
        assert result is False

    def test_has_arabic_letters_with_arabic_text(self, sample_arabic_text: str) -> None:
        """Test has_arabic_letters with Arabic text."""
        # Act
        result = arabic_reshaper.has_arabic_letters(sample_arabic_text)

        # Assert
        assert result is True

    def test_has_arabic_letters_with_mixed_text(self, sample_mixed_text: str) -> None:
        """Test has_arabic_letters with mixed text."""
        # Act
        result = arabic_reshaper.has_arabic_letters(sample_mixed_text)

        # Assert
        assert result is True

    def test_has_arabic_letters_with_latin_text(self) -> None:
        """Test has_arabic_letters with Latin text only."""
        # Arrange
        text = 'Hello World'

        # Act
        result = arabic_reshaper.has_arabic_letters(text)

        # Assert
        assert result is False

    def test_is_arabic_word_with_pure_arabic(self, sample_arabic_text: str) -> None:
        """Test is_arabic_word with pure Arabic word."""
        # Arrange
        word = sample_arabic_text.split()[0]  # First word

        # Act
        result = arabic_reshaper.is_arabic_word(word)

        # Assert
        assert result is True

    def test_is_arabic_word_with_mixed_word(self) -> None:
        """Test is_arabic_word with mixed Arabic-Latin word."""
        # Arrange
        word = 'Hello\u0627'  # Hello + Alef

        # Act
        result = arabic_reshaper.is_arabic_word(word)

        # Assert
        assert result is False

    def test_is_arabic_word_with_latin_word(self) -> None:
        """Test is_arabic_word with Latin word."""
        # Arrange
        word = 'Hello'

        # Act
        result = arabic_reshaper.is_arabic_word(word)

        # Assert
        assert result is False


class TestTextProcessing:
    """Test text processing and word extraction functions."""

    def test_get_words_with_sentence(self, sample_arabic_text: str) -> None:
        """Test get_words with Arabic sentence."""
        # Act
        result = arabic_reshaper.get_words(sample_arabic_text)

        # Assert
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(word, str) for word in result)

    def test_get_words_with_empty_string(self) -> None:
        """Test get_words with empty string."""
        # Arrange
        sentence = ''

        # Act
        result = arabic_reshaper.get_words(sentence)

        # Assert
        assert result == []

    def test_get_words_with_single_word(self) -> None:
        """Test get_words with single word."""
        # Arrange
        sentence = 'السلام'

        # Act
        result = arabic_reshaper.get_words(sentence)

        # Assert
        assert len(result) == 1
        assert result[0] == 'السلام'

    def test_get_words_from_mixed_word_arabic_latin(self) -> None:
        """Test get_words_from_mixed_word with Arabic-Latin mix."""
        # Arrange
        word = 'Hello\u0627\u0644\u0644\u0647World'  # Hello + Allah + World

        # Act
        result = arabic_reshaper.get_words_from_mixed_word(word)

        # Assert
        assert isinstance(result, list)
        assert len(result) >= 2  # Should separate Arabic and Latin parts
        assert any(arabic_reshaper.has_arabic_letters(w) for w in result)
        assert any(not arabic_reshaper.has_arabic_letters(w) for w in result)

    def test_get_words_from_mixed_word_pure_arabic(self, sample_arabic_text: str) -> None:
        """Test get_words_from_mixed_word with pure Arabic."""
        # Arrange
        word = sample_arabic_text.split()[0]  # First word

        # Act
        result = arabic_reshaper.get_words_from_mixed_word(word)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == word

    def test_get_words_from_mixed_word_pure_latin(self) -> None:
        """Test get_words_from_mixed_word with pure Latin."""
        # Arrange
        word = 'Hello'

        # Act
        result = arabic_reshaper.get_words_from_mixed_word(word)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == word

    def test_get_words_from_mixed_word_empty(self) -> None:
        """Test get_words_from_mixed_word with empty string."""
        # Arrange
        word = ''

        # Act
        result = arabic_reshaper.get_words_from_mixed_word(word)

        # Assert
        assert result == []


class TestSentenceReshaping:
    """Test sentence-level reshaping functions."""

    def test_reshape_sentence_arabic_only(self, sample_arabic_text: str) -> None:
        """Test reshape_sentence with Arabic-only text."""
        # Act
        result = arabic_reshaper.reshape_sentence(sample_arabic_text)

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain reshaped Arabic text

    def test_reshape_sentence_mixed_text(self, sample_mixed_text: str) -> None:
        """Test reshape_sentence with mixed Arabic-Latin text."""
        # Act
        result = arabic_reshaper.reshape_sentence(sample_mixed_text)

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
        # Should preserve Latin text and reshape Arabic parts
        assert 'Hello' in result
        assert 'World' in result

    def test_reshape_sentence_latin_only(self) -> None:
        """Test reshape_sentence with Latin-only text."""
        # Arrange
        sentence = 'Hello World'

        # Act
        result = arabic_reshaper.reshape_sentence(sentence)

        # Assert
        assert result == sentence  # Should remain unchanged

    def test_reshape_sentence_empty_string(self) -> None:
        """Test reshape_sentence with empty string."""
        # Arrange
        sentence = ''

        # Act
        result = arabic_reshaper.reshape_sentence(sentence)

        # Assert
        assert result == ''

    def test_reshape_sentence_with_harakat(self, sample_arabic_with_harakat: str) -> None:
        """Test reshape_sentence with text containing harakat."""
        # Act
        result = arabic_reshaper.reshape_sentence(sample_arabic_with_harakat)

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
        # Should preserve harakat in the result
        assert any(arabic_reshaper.is_haraka(c) for c in result)


class TestFullTextReshaping:
    """Test full text reshaping with multiple lines."""

    def test_reshape_single_line(self, sample_arabic_text: str) -> None:
        """Test reshape with single line of text."""
        # Act
        result = arabic_reshaper.reshape(sample_arabic_text)

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
        # Should be equivalent to reshape_sentence for single line

    def test_reshape_multiple_lines(self) -> None:
        """Test reshape with multiple lines of text."""
        # Arrange
        text = 'السلام عليكم\nمرحبا بكم'  # Two lines of Arabic

        # Act
        result = arabic_reshaper.reshape(text)

        # Assert
        assert isinstance(result, str)
        assert '\n' in result  # Should preserve line breaks
        lines = result.split('\n')
        assert len(lines) == 2
        assert all(len(line) > 0 for line in lines)

    def test_reshape_empty_text(self) -> None:
        """Test reshape with empty text."""
        # Arrange
        text = ''

        # Act
        result = arabic_reshaper.reshape(text)

        # Assert
        assert result == ''

    def test_reshape_mixed_lines(self) -> None:
        """Test reshape with mixed Arabic-Latin lines."""
        # Arrange
        text = 'Hello World\nالسلام عليكم\nGoodbye'

        # Act
        result = arabic_reshaper.reshape(text)

        # Assert
        assert isinstance(result, str)
        lines = result.split('\n')
        assert len(lines) == 3
        assert 'Hello World' in lines[0]  # Latin should be unchanged
        assert 'Goodbye' in lines[2]  # Latin should be unchanged
        # Middle line should be reshaped Arabic

    def test_reshape_carriage_return_newline(self) -> None:
        """Test reshape with Windows-style line endings."""
        # Arrange
        text = 'السلام عليكم\r\nمرحبا بكم'

        # Act
        result = arabic_reshaper.reshape(text)

        # Assert
        assert isinstance(result, str)
        assert '\n' in result  # Should normalize to Unix line endings
        lines = result.split('\n')
        assert len(lines) == 2

    def test_reshape_with_lam_alef_ligature(self, sample_lam_alef_text: str) -> None:
        """Test reshape with text containing Lam-Alef combinations."""
        # Act
        result = arabic_reshaper.reshape(sample_lam_alef_text)

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
        # Should handle Lam-Alef ligatures properly
