#
# This work is licensed under the GNU Public License (GPL).
# To view a copy of this license, visit http://www.gnu.org/copyleft/gpl.html

# Written by Abd Allah Diab (mpcabd)
# Email: mpcabd ^at^ gmail ^dot^ com
# Website: http://mpcabd.igeex.biz

# Ported and tweaked from Java to Python, from Better Arabic Reshaper [https://github.com/agawish/Better-Arabic-Reshaper/]

import re

DEFINED_CHARACTERS_ORGINAL_ALF_UPPER_MDD        = '\u0622'
DEFINED_CHARACTERS_ORGINAL_ALF_UPPER_HAMAZA     = '\u0623'
DEFINED_CHARACTERS_ORGINAL_ALF_LOWER_HAMAZA     = '\u0625'
DEFINED_CHARACTERS_ORGINAL_ALF                  = '\u0627'
DEFINED_CHARACTERS_ORGINAL_LAM                  = '\u0644'

LAM_ALEF_GLYPHS = [
    ['\u3BA6', '\uFEF6', '\uFEF5'],
    ['\u3BA7', '\uFEF8', '\uFEF7'],
    ['\u0627', '\uFEFC', '\uFEFB'],
    ['\u0625', '\uFEFA', '\uFEF9']
]

HARAKAT = [
    '\u0600', '\u0601', '\u0602', '\u0603', '\u0606', '\u0607', '\u0608', '\u0609',
    '\u060A', '\u060B', '\u060D', '\u060E', '\u0610', '\u0611', '\u0612', '\u0613',
    '\u0614', '\u0615', '\u0616', '\u0617', '\u0618', '\u0619', '\u061A', '\u061B',
    '\u061E', '\u061F', '\u0621', '\u063B', '\u063C', '\u063D', '\u063E', '\u063F',
    '\u0640', '\u064B', '\u064C', '\u064D', '\u064E', '\u064F', '\u0650', '\u0651',
    '\u0652', '\u0653', '\u0654', '\u0655', '\u0656', '\u0657', '\u0658', '\u0659',
    '\u065A', '\u065B', '\u065C', '\u065D', '\u065E', '\u0660', '\u066A', '\u066B',
    '\u066C', '\u066F', '\u0670', '\u0672', '\u06D4', '\u06D5', '\u06D6', '\u06D7',
    '\u06D8', '\u06D9', '\u06DA', '\u06DB', '\u06DC', '\u06DF', '\u06E0', '\u06E1',
    '\u06E2', '\u06E3', '\u06E4', '\u06E5', '\u06E6', '\u06E7', '\u06E8', '\u06E9',
    '\u06EA', '\u06EB', '\u06EC', '\u06ED', '\u06EE', '\u06EF', '\u06D6', '\u06D7',
    '\u06D8', '\u06D9', '\u06DA', '\u06DB', '\u06DC', '\u06DD', '\u06DE', '\u06DF',
    '\u06F0', '\u06FD', '\uFE70', '\uFE71', '\uFE72', '\uFE73', '\uFE74', '\uFE75',
    '\uFE76', '\uFE77', '\uFE78', '\uFE79', '\uFE7A', '\uFE7B', '\uFE7C', '\uFE7D',
    '\uFE7E', '\uFE7F', '\uFC5E', '\uFC5F', '\uFC60', '\uFC61', '\uFC62', '\uFC63'
]

ARABIC_GLYPHS = {
    '\u0622' : ['\u0622', '\uFE81', '\uFE81', '\uFE82', '\uFE82', 2],
    '\u0623' : ['\u0623', '\uFE83', '\uFE83', '\uFE84', '\uFE84', 2],
    '\u0624' : ['\u0624', '\uFE85', '\uFE85', '\uFE86', '\uFE86', 2],
    '\u0625' : ['\u0625', '\uFE87', '\uFE87', '\uFE88', '\uFE88', 2],
    '\u0626' : ['\u0626', '\uFE89', '\uFE8B', '\uFE8C', '\uFE8A', 4],
    '\u0627' : ['\u0627', '\u0627', '\u0627', '\uFE8E', '\uFE8E', 2],
    '\u0628' : ['\u0628', '\uFE8F', '\uFE91', '\uFE92', '\uFE90', 4],
    '\u0629' : ['\u0629', '\uFE93', '\uFE93', '\uFE94', '\uFE94', 2],
    '\u062A' : ['\u062A', '\uFE95', '\uFE97', '\uFE98', '\uFE96', 4],
    '\u062B' : ['\u062B', '\uFE99', '\uFE9B', '\uFE9C', '\uFE9A', 4],
    '\u062C' : ['\u062C', '\uFE9D', '\uFE9F', '\uFEA0', '\uFE9E', 4],
    '\u062D' : ['\u062D', '\uFEA1', '\uFEA3', '\uFEA4', '\uFEA2', 4],
    '\u062E' : ['\u062E', '\uFEA5', '\uFEA7', '\uFEA8', '\uFEA6', 4],
    '\u062F' : ['\u062F', '\uFEA9', '\uFEA9', '\uFEAA', '\uFEAA', 2],
    '\u0630' : ['\u0630', '\uFEAB', '\uFEAB', '\uFEAC', '\uFEAC', 2],
    '\u0631' : ['\u0631', '\uFEAD', '\uFEAD', '\uFEAE', '\uFEAE', 2],
    '\u0632' : ['\u0632', '\uFEAF', '\uFEAF', '\uFEB0', '\uFEB0', 2],
    '\u0633' : ['\u0633', '\uFEB1', '\uFEB3', '\uFEB4', '\uFEB2', 4],
    '\u0634' : ['\u0634', '\uFEB5', '\uFEB7', '\uFEB8', '\uFEB6', 4],
    '\u0635' : ['\u0635', '\uFEB9', '\uFEBB', '\uFEBC', '\uFEBA', 4],
    '\u0636' : ['\u0636', '\uFEBD', '\uFEBF', '\uFEC0', '\uFEBE', 4],
    '\u0637' : ['\u0637', '\uFEC1', '\uFEC3', '\uFEC4', '\uFEC2', 4],
    '\u0638' : ['\u0638', '\uFEC5', '\uFEC7', '\uFEC8', '\uFEC6', 4],
    '\u0639' : ['\u0639', '\uFEC9', '\uFECB', '\uFECC', '\uFECA', 4],
    '\u063A' : ['\u063A', '\uFECD', '\uFECF', '\uFED0', '\uFECE', 4],
    '\u0641' : ['\u0641', '\uFED1', '\uFED3', '\uFED4', '\uFED2', 4],
    '\u0642' : ['\u0642', '\uFED5', '\uFED7', '\uFED8', '\uFED6', 4],
    '\u0643' : ['\u0643', '\uFED9', '\uFEDB', '\uFEDC', '\uFEDA', 4],
    '\u0644' : ['\u0644', '\uFEDD', '\uFEDF', '\uFEE0', '\uFEDE', 4],
    '\u0645' : ['\u0645', '\uFEE1', '\uFEE3', '\uFEE4', '\uFEE2', 4],
    '\u0646' : ['\u0646', '\uFEE5', '\uFEE7', '\uFEE8', '\uFEE6', 4],
    '\u0647' : ['\u0647', '\uFEE9', '\uFEEB', '\uFEEC', '\uFEEA', 4],
    '\u0648' : ['\u0648', '\uFEED', '\uFEED', '\uFEEE', '\uFEEE', 2],
    '\u0649' : ['\u0649', '\uFEEF', '\uFEEF', '\uFEF0', '\uFEF0', 2],
    '\u0671' : ['\u0671', '\u0671', '\u0671', '\uFB51', '\uFB51', 2],
    '\u064A' : ['\u064A', '\uFEF1', '\uFEF3', '\uFEF4', '\uFEF2', 4],
    '\u066E' : ['\u066E', '\uFBE4', '\uFBE8', '\uFBE9', '\uFBE5', 4],
    '\u06AA' : ['\u06AA', '\uFB8E', '\uFB90', '\uFB91', '\uFB8F', 4],
    '\u06C1' : ['\u06C1', '\uFBA6', '\uFBA8', '\uFBA9', '\uFBA7', 4],
    '\u06E4' : ['\u06E4', '\u06E4', '\u06E4', '\u06E4', '\uFEEE', 2],
    '\u067E' : ['\u067E', '\uFB56', '\uFB58', '\uFB59', '\uFB57', 4],
    '\u0698' : ['\u0698', '\uFB8A', '\uFB8A', '\uFB8A', '\uFB8B', 2],
    '\u06AF' : ['\u06AF', '\uFB92', '\uFB94', '\uFB95', '\uFB93', 4],
    '\u0686' : ['\u0686', '\uFB7A', '\uFB7C', '\uFB7D', '\uFB7B', 4],
    '\u06A9' : ['\u06A9', '\uFB8E', '\uFB90', '\uFB91', '\uFB8F', 4],
    '\u06CC' : ['\u06CC', '\uFEEF', '\uFEF3', '\uFEF4', '\uFEF0', 4]
}

ARABIC_GLYPHS_LIST = [
    ['\u0622', '\uFE81', '\uFE81', '\uFE82', '\uFE82', 2],
    ['\u0623', '\uFE83', '\uFE83', '\uFE84', '\uFE84', 2],
    ['\u0624', '\uFE85', '\uFE85', '\uFE86', '\uFE86', 2],
    ['\u0625', '\uFE87', '\uFE87', '\uFE88', '\uFE88', 2],
    ['\u0626', '\uFE89', '\uFE8B', '\uFE8C', '\uFE8A', 4],
    ['\u0627', '\u0627', '\u0627', '\uFE8E', '\uFE8E', 2],
    ['\u0628', '\uFE8F', '\uFE91', '\uFE92', '\uFE90', 4],
    ['\u0629', '\uFE93', '\uFE93', '\uFE94', '\uFE94', 2],
    ['\u062A', '\uFE95', '\uFE97', '\uFE98', '\uFE96', 4],
    ['\u062B', '\uFE99', '\uFE9B', '\uFE9C', '\uFE9A', 4],
    ['\u062C', '\uFE9D', '\uFE9F', '\uFEA0', '\uFE9E', 4],
    ['\u062D', '\uFEA1', '\uFEA3', '\uFEA4', '\uFEA2', 4],
    ['\u062E', '\uFEA5', '\uFEA7', '\uFEA8', '\uFEA6', 4],
    ['\u062F', '\uFEA9', '\uFEA9', '\uFEAA', '\uFEAA', 2],
    ['\u0630', '\uFEAB', '\uFEAB', '\uFEAC', '\uFEAC', 2],
    ['\u0631', '\uFEAD', '\uFEAD', '\uFEAE', '\uFEAE', 2],
    ['\u0632', '\uFEAF', '\uFEAF', '\uFEB0', '\uFEB0', 2],
    ['\u0633', '\uFEB1', '\uFEB3', '\uFEB4', '\uFEB2', 4],
    ['\u0634', '\uFEB5', '\uFEB7', '\uFEB8', '\uFEB6', 4],
    ['\u0635', '\uFEB9', '\uFEBB', '\uFEBC', '\uFEBA', 4],
    ['\u0636', '\uFEBD', '\uFEBF', '\uFEC0', '\uFEBE', 4],
    ['\u0637', '\uFEC1', '\uFEC3', '\uFEC4', '\uFEC2', 4],
    ['\u0638', '\uFEC5', '\uFEC7', '\uFEC8', '\uFEC6', 4],
    ['\u0639', '\uFEC9', '\uFECB', '\uFECC', '\uFECA', 4],
    ['\u063A', '\uFECD', '\uFECF', '\uFED0', '\uFECE', 4],
    ['\u0641', '\uFED1', '\uFED3', '\uFED4', '\uFED2', 4],
    ['\u0642', '\uFED5', '\uFED7', '\uFED8', '\uFED6', 4],
    ['\u0643', '\uFED9', '\uFEDB', '\uFEDC', '\uFEDA', 4],
    ['\u0644', '\uFEDD', '\uFEDF', '\uFEE0', '\uFEDE', 4],
    ['\u0645', '\uFEE1', '\uFEE3', '\uFEE4', '\uFEE2', 4],
    ['\u0646', '\uFEE5', '\uFEE7', '\uFEE8', '\uFEE6', 4],
    ['\u0647', '\uFEE9', '\uFEEB', '\uFEEC', '\uFEEA', 4],
    ['\u0648', '\uFEED', '\uFEED', '\uFEEE', '\uFEEE', 2],
    ['\u0649', '\uFEEF', '\uFEEF', '\uFEF0', '\uFEF0', 2],
    ['\u0671', '\u0671', '\u0671', '\uFB51', '\uFB51', 2],
    ['\u064A', '\uFEF1', '\uFEF3', '\uFEF4', '\uFEF2', 4],
    ['\u066E', '\uFBE4', '\uFBE8', '\uFBE9', '\uFBE5', 4],
    ['\u06AA', '\uFB8E', '\uFB90', '\uFB91', '\uFB8F', 4],
    ['\u06C1', '\uFBA6', '\uFBA8', '\uFBA9', '\uFBA7', 4],
    ['\u067E', '\uFB56', '\uFB58', '\uFB59', '\uFB57', 4],
    ['\u0698', '\uFB8A', '\uFB8A', '\uFB8A', '\uFB8B', 2],
    ['\u06AF', '\uFB92', '\uFB94', '\uFB95', '\uFB93', 4],
    ['\u0686', '\uFB7A', '\uFB7C', '\uFB7D', '\uFB7B', 4],
    ['\u06A9', '\uFB8E', '\uFB90', '\uFB91', '\uFB8F', 4],
    ['\u06CC', '\uFEEF', '\uFEF3', '\uFEF4', '\uFEF0', 4]
]

def get_reshaped_glyph(target, location):
    if target in ARABIC_GLYPHS:
        return ARABIC_GLYPHS[target][location]
    return target

def get_glyph_type(target):
    if target in ARABIC_GLYPHS:
        return ARABIC_GLYPHS[target][5]
    return 2

def is_haraka(target):
    return target in HARAKAT

def replace_jalalah(unshaped_word):
    return re.sub('^\u0627\u0644\u0644\u0647$', '\uFDF2', unshaped_word)

def replace_lam_alef(unshaped_word):
    list_word = list(unshaped_word)
    letter_before = ''
    for i, _ in enumerate(unshaped_word):
        if not is_haraka(unshaped_word[i]) and unshaped_word[i] != DEFINED_CHARACTERS_ORGINAL_LAM:
            letter_before = unshaped_word[i]

        if unshaped_word[i] == DEFINED_CHARACTERS_ORGINAL_LAM:
            candidate_lam = unshaped_word[i]
            lam_position = i
            haraka_position = i + 1

            while haraka_position < len(unshaped_word) and is_haraka(unshaped_word[haraka_position]):
                haraka_position += 1

            if haraka_position < len(unshaped_word):
                if lam_position > 0 and get_glyph_type(letter_before) > 2:
                    lam_alef = get_lam_alef(list_word[haraka_position], candidate_lam, False)
                else:
                    lam_alef = get_lam_alef(list_word[haraka_position], candidate_lam, True)
                if lam_alef != '':
                    list_word[lam_position] = lam_alef
                    list_word[haraka_position] = ' '

    return ''.join(list_word).replace(' ', '')

def get_lam_alef(candidate_alef, candidate_lam, is_end_of_word):
    shift_rate = 1
    if is_end_of_word:
        shift_rate += 1

    if candidate_lam == DEFINED_CHARACTERS_ORGINAL_LAM:
        if candidate_alef == DEFINED_CHARACTERS_ORGINAL_ALF_UPPER_MDD:
            return LAM_ALEF_GLYPHS[0][shift_rate]

        if candidate_alef == DEFINED_CHARACTERS_ORGINAL_ALF_UPPER_HAMAZA:
            return LAM_ALEF_GLYPHS[1][shift_rate]

        if candidate_alef == DEFINED_CHARACTERS_ORGINAL_ALF:
            return LAM_ALEF_GLYPHS[2][shift_rate]

        if candidate_alef == DEFINED_CHARACTERS_ORGINAL_ALF_LOWER_HAMAZA:
            return LAM_ALEF_GLYPHS[3][shift_rate]

    return ''

class DecomposedWord(): # pylint: disable=too-few-public-methods
    def __init__(self, word) -> None:
        self.stripped_harakat = []
        self.harakat_positions = []
        self.stripped_regular_letters = []
        self.letters_position = []

        for i, _ in enumerate(word):
            c = word[i]
            if is_haraka(c):
                self.harakat_positions.append(i)
                self.stripped_harakat.append(c)
            else:
                self.letters_position.append(i)
                self.stripped_regular_letters.append(c)

    def reconstruct_word(self, reshaped_word):
        ll = list('\x00' * (len(self.stripped_harakat) + len(reshaped_word)))
        for i, _ in enumerate(self.letters_position):
            ll[self.letters_position[i]] = reshaped_word[i]
        for i, _ in enumerate(self.harakat_positions):
            ll[self.harakat_positions[i]] = self.stripped_harakat[i]
        return ''.join(ll)

def get_reshaped_word(unshaped_word):
    unshaped_word = replace_jalalah(unshaped_word)
    unshaped_word = replace_lam_alef(unshaped_word)
    decomposed_word = DecomposedWord(unshaped_word)
    result = ''
    if decomposed_word.stripped_regular_letters:
        result = reshape_it(''.join(decomposed_word.stripped_regular_letters))
    return decomposed_word.reconstruct_word(result)

def reshape_it(unshaped_word):
    if not unshaped_word:
        return ''
    if len(unshaped_word) == 1:
        return get_reshaped_glyph(unshaped_word[0], 1)
    reshaped_word = []
    for i, _ in enumerate(unshaped_word):
        before = False
        after = False
        if i == 0:
            after = get_glyph_type(unshaped_word[i]) == 4
        elif i == len(unshaped_word) - 1:
            before = get_glyph_type(unshaped_word[i - 1]) == 4
        else:
            after = get_glyph_type(unshaped_word[i]) == 4
            before = get_glyph_type(unshaped_word[i - 1]) == 4
        if after and before:
            reshaped_word.append(get_reshaped_glyph(unshaped_word[i], 3))
        elif after and not before:
            reshaped_word.append(get_reshaped_glyph(unshaped_word[i], 2))
        elif not after and before:
            reshaped_word.append(get_reshaped_glyph(unshaped_word[i], 4))
        elif not after and not before:
            reshaped_word.append(get_reshaped_glyph(unshaped_word[i], 1))

    return ''.join(reshaped_word)


def is_arabic_character(target):
    return target in ARABIC_GLYPHS or target in HARAKAT

def get_words(sentence):
    if sentence:
        return re.split('\\s', sentence)
    return []

def has_arabic_letters(word):
    return any(is_arabic_character(c) for c in word)

def is_arabic_word(word):
    return all(is_arabic_character(c) for c in word)

def get_words_from_mixed_word(word):
    temp_word = ''
    words = []
    for c in word:
        if is_arabic_character(c):
            if temp_word and not is_arabic_word(temp_word):
                words.append(temp_word)
                temp_word = c
            else:
                temp_word += c
        elif temp_word and is_arabic_word(temp_word):
            words.append(temp_word)
            temp_word = c
        else:
            temp_word += c
    if temp_word:
        words.append(temp_word)
    return words

def reshape(text):
    if text:
        lines = re.split('\\r?\\n', text)
        for i, _ in enumerate(lines):
            lines[i] = reshape_sentence(lines[i])
        return '\n'.join(lines)
    return ''

def reshape_sentence(sentence):
    words = get_words(sentence)
    for i, _ in enumerate(words):
        word = words[i]
        if has_arabic_letters(word):
            if is_arabic_word(word):
                words[i] = get_reshaped_word(word)
            else:
                mixed_words = get_words_from_mixed_word(word)
                for j, _ in enumerate(mixed_words):
                    mixed_words[j] = get_reshaped_word(mixed_words[j])
                words[i] = ''.join(mixed_words)
    return ' '.join(words)
