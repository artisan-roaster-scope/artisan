# How to provide or improve translations

____
**Important: Artisan is licensed under [The GNU General Public License](https://www.gnu.org/licenses/gpl-3.0.html).  Copies of Artisan and derivative works are subject to this license.  Be sure to review the license to understand your legal obligations and please respect them.**
____

### Introduction

Artisan UI, including menu items and button labels, is written in English. Artisan utilizes Qt `.ts` files for localization, enabling its UI to be displayed in various languages. These `.ts` files containing the translations of the UI are text files formatted in XML. During the Artisan build process, these `.ts` files are compiled into the more efficient `.qm` binary format, which Artisan employs to localize its UI during runtime.

### Updating translations

To update translations for a specific language, you must follow three steps.

#### 1. identify and download the translation file

First, you need to identify and download the `.ts` file containing the translations corresponding to that specific language.

The translation files are named `artisan_xx.ts` and can be found on GitHub in the [`src/translations`](https://github.com/artisan-roaster-scope/artisan/tree/master/src/translations) subfolder. The `xx` indicates the language, which is determined by the [ISO 639-1](https://en.wikipedia.org/wiki/ISO_639-1) Alpha-2 code. Some files are further qualified by an additional code that specifies the language version. Currently, Artisan supports the following languages.


ISO-2 Code         | Language         |
-------------------|------------------|
ar | Arabic |
bg | Bulgarian |
cs | Czech |
da | Danish |
de | German |
el | Greek |
es | Spanish |
fa | Persian |
fi | Finnish |
fr | French |
gd | Scottish Gaelic  |
he | Hebrew |
hu | Hungarian |
id | Indonesian |
it | Italian |
ja | Japanese |
ko | Korean |
lv | Latvian |
nl | Dutch |
no | Norwegian |
pl | Polish |
pt_BR | Portuguese, Brazilian |
pt | Portuguese, European |
ru | Russian |
sk | Slovak |
sv | Swedish |
th | Thai |
tr | Turkish |
uk | Ukrainian |
vi | Vietnamese |
zh_CN | Chinese, Simplified |
zh_TW | Chinese, Traditional |

If there's no `.ts` file for the language you'd like translations for, please open an issue on the [Artisan tracker on GitHub](https://github.com/artisan-roaster-scope/artisan/issues) requesting the initial infrastructure for that new language.


#### 2. update the translations

Using a text editor (without breaking the XML format) or, preferably, the [Qt Linguist](https://doc.qt.io/archives/qt-5.15/qtlinguist-index.html) app is recommended. The Linguist app for Windows can be downloaded at the time of writing [here](https://github.com/thurask/Qt-Linguist/releases). There are also macOS and Linux versions available as part of any Qt release and as separate downloads.

Providing translations for the Artisan UI is a monumental task, involving 3684 sentences! However, not all sentences hold equal importance.

Sentences are grouped into so-called contexts, as follows. The most crucial groups are highlighted in bold.

Context         | Purpose         |
----------------|--------------|
About | About dialog |
AddlInfo | Profile info dialog |
__Button__ | __button labels__ |
__CheckBox__ | __check box labels__ |
__ComboBox__ | __combo box items__ |
Contextual Menu | popup menu items |
Countries | countrie names |
Dialog | dialog titles |
Error Message | messages of the error log |
__Form Caption__ | __dialog titles__ |
__GroupBox__ | __titles of widget groups__ |
HTML Report Template | tags of HTML reports |
HelpDlg | help dialog text elements |
__Label__ | __widget labels__ |
__MAC\_APPLICATION\_MENU__ | __macOS specific menu items__ |
Marker | chart marker names |
__Menu__ | __menu names__ |
Message | status messages |
Plus | artisan.plus related labels |
__Radio Button__ | __radio button labels__ |
__Scope Annotation__ | profile annotations |
__Scope Title__ | __funny default profile title__ |
StatusBar | status bar messages |
__Tab__ | __tab labels__ |
__Table__ | __labels used in tables__ |
Textbox | cupping related labels |
Toolbar | toolbar labels |
Tooltip | tooltip messages |

__Notes__

- Items marked as `obsolete` are no longer in use and don't require translation.
- There are sentences with substitutions, such as `sponsored by {}` or `MS6514temperature(): {0} bytes received but 18 needed`. In these cases, the curly brackets represent placeholders that are dynamically replaced by a translated phrase during runtime. It's crucial to retain these placeholders in the translations.


#### 3. provide the updated `.ts` file back to the project for integration

After adding new translations or improving existing ones, save your work again as a `.ts` file. You can send it back to the project by forking the project on GitHub and creating a pull request (PR), or, for a simpler option, open an issue or discussion item and attach the file (renamed to end in `.ts.txt`) by dragging and dropping it into a comment field on the GitHub web page.

We will integrate your work and generate new builds for you to verify the result.

Thanks for your contributions!
_The Artisan team_
