# Codoscope

Visualize the python compile pipeline

Based in https://github.com/iritkatriel/codoscope/tree/main

## Install instructions

This requires:

* Python 3.13 (tested with 3.13.0b1)
* dependencies in requirements.txt
  * You will have to install `typing_extensions` from the main branch (4.11.0 doesn't work in 3.13)
  * You will have to manually install `tree-sitter-languages` manually ([Clone this](https://github.com/grantjenks/py-tree-sitter-languages/tree/main) and run `./setup.py install`; there are no wheels for 3.13). Doing this will require Cython (which you can `pip install`)

The code uses internal, undocumented APIs. It is very likely to break in future Python versions.
When it does you get to keep both pieces.

If you run this under python 3.12 or lower, you will get reduced functionality.