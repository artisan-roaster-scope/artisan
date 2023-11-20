# Installing Artisan to run from source

## macOS/Linux/Windows

### Installation

1. Install git from [scm-git.com](https://git-scm.com/downloads)

2. Install Python 3.11 from [python.org](https://www.python.org/)

   >*Note for Windows: When Python is installed by direct download it is normally started with the command `python`.  When installed from Microsoft Store it is normally started using `python3` as shown below. Also note, the Windows command prompt is '>' where the macOS/Linux prompt is '#' as shown below.*


3. Create and activate a virtual environment

    ```
    # python3 -m venv artisan_venv
    # source artisan_venv/bin/activate
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

6. Build derived artifacts

    macOS/Linux
    ```
    # ./build-derived.sh
    ```
    Windows

    ```
    > build-derived-win.bat
    ```


7. Start Artisan

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


