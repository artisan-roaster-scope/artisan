# Installing Artisan to run from source

## macOS/Linux

### Installation

1. Install Python 3.11 from [python.org](https://www.python.org/)

2. Create and activate a virtual environment

    ```
    # python3 -m venv artisan_venv
    # source artisan_venv/bin/activate
    ```

3. Clone the Artisan repository

    ```
    # git clone https://github.com/artisan-roaster-scope/artisan.git
    ```

4. Install required packages

    ```
    # cd artisan/src
    # pip install -r requirements.txt
    ```

5. Build derived artefacts

    ```
    # ./build-derived.sh
    ```

6. Start Artisan

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



## Windows


tobedone
