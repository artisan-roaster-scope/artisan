# How to run Artisan from source

____
**Important: Artisan is licensed under [The GNU General Public License](https://www.gnu.org/licenses/gpl-3.0.html).  Copies of Artisan and derivative works are subject to this license.  Be sure to review the license to understand your legal obligations and please respect them.**  
____

### Introduction

Artisan provides install packages for all supported platforms on [GitHub](https://github.com/artisan-roaster-scope/artisan/releases).  However, some users may desire to run Artisan directly from the source code.  This document explains how to do so on macOS, Linux and Windows. 

While this document is presumed free of errors as of January 2024, there is no guarantee that it is correct as you read it.  If you find an error or discrepancy please start a [new general discussion](https://github.com/artisan-roaster-scope/artisan/discussions/new?category=general) on GitHub.


### Installation on macOS/Linux/Windows

1. Install git from [scm-git.com](https://git-scm.com/downloads)

2. Install Python 3.11 from [python.org](https://www.python.org/)

   >*Note for Windows: Python may also be installed from the Microsoft Store or by direct download from the link above.  When installed from the Microsoft Store it is normally started using `python3` as shown below.  When Python is installed by direct download it is normally started with the command `python`. Also note, the Windows command prompt is '>' where the macOS/Linux prompt is '#' as shown below.*


3. Create and activate a virtual environment

    macOS and Linux
    ```
    # python3 -m venv artisan_venv
    # source artisan_venv/bin/activate
    ```

    Windows
    ```
    > python3 -m venv artisan_venv
    > artisan_venv\scripts\activate
    ```

4. Clone the Artisan repository

    ```
    # git clone https://github.com/artisan-roaster-scope/artisan.git
    ```

5. Install required packages

    ```
    # cd artisan/src
    # pip install -r requirements.txt
    ```

[comment]: # (Removing this section for now.  To restore delete each comment line and one blank line immediately above it.)

[comment]: # (6. Build derived artifacts)


[comment]: # (    macOS/Linux)

[comment]: # (    ```)

[comment]: # (    # ./build-derived.sh)

[comment]: # (    ```)

[comment]: # (    Windows)


[comment]: # (    ```)

[comment]: # (    > build-derived-win.bat)

[comment]: # (    ```)

[comment]: # (When restoring change the nu,ber below to '7')

6. Start Artisan from the artisan/src directory. 

   ```
   # python3 artisan.py
   ```

### Application log

- macOS

   ```
   # tail -f ~/Library/Application\ Support/artisan-scope/Artisan/artisan.log
   ```

- Linux

   ```
   # tail -f ~/.local/shared/artisan-scope/Artisan/artisan.log
   ```
 - Windows

   ```
   > notepad %localappdata%\artisan-scope\Artisan\artisan.log
   ```


### Installing and running dev tools

```
# pip install -r requirements-dev.txt
```

Linting


```
# codespell
# ruff check .
# pylint */*.py
```

Typing

```
# mypy
# pyright
# mypy --strict
```

Testing


```
# pytest
```

Coverage (types, tests)

```
# mypy --xslt-html-report coverage
# pytest --cov --cov-report=html
# pytest --hypothesis-show-statistics
# coverage run -m pytest
# coverage-badge -o coverage.svg
```


