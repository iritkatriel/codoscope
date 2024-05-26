# Codoscope

Visualize the python compile pipeline

Based in https://github.com/iritkatriel/codoscope/tree/main

## Install

This requires:

* CPython 3.13 (tested with 3.13.0b1)
* dependencies in requirements.txt
  * You will have to manually install `tree-sitter-languages` manually to have syntax
    highlighting. See step-by-step instructions below

The code uses internal, undocumented CPython APIs. It is very likely to break in future
CPython versions. When it does you get to keep both pieces.

You can run this code under python 3.12 or lower, but many features will be disabled.

### Step by step

The code is not packaged, due to some dependencies not being available yet in
Python 3.13 (See [this issue](https://github.com/grantjenks/py-tree-sitter-languages/issues/66)).
I was able to get everything up by running the following commands:


```sh
python3.13 -m venv env
git clone https://github.com/grantjenks/py-tree-sitter-languages.git
git clone https://github.com/dmoisset/codoscope.git
../env/bin/pip install
cd py-tree-sitter-languages/
../env/bin/pip install Cython tree_sitter==0.20.4 setuptools
../env/bin/python build.py
../env/bin/python setup.py install
cd ../codoscope
../env/bin/pip install -r requirements.txt
```

## Usage

```sh
env/bin/python codoscope/src/main.py
```

Will start the application. You can press `e` to edit the code, and `CTRL+S` to go back
to the inspector. You can enable different code views in the inspectors with the numbers
from `1` to `7`. You can quit with `q`

You can pre-load source from a file by running:

```sh
env/bin/python codoscope/src/main.py source-file-to-analyze.py
```

For testing compilation of a single line you can use:

```sh
env/bin/python codoscope/src/main.py -c 'x = [y*y for y in range(10)]'
```

For showing the code of a python module you can run:

```sh
env/bin/python codoscope/src/main.py -m package.module
```
