Installation
============

Requirements
------------

- Python 3.10 or newer for the 0.x release series.
- No third-party runtime packages.
- No API key or network access after installation.

Published package
-----------------

PyPI releases earlier than 0.2.0 belong to the legacy prototype and are not
compatible with the examples in this documentation. Confirm that 0.2.0 is in
the release history, then install the exact version:

.. code-block:: console

   python -m pip install pyworldatlas==0.2.0

Install this checkout in VS Code
--------------------------------

Open the project folder, select a Python interpreter, create a ``.venv``, and
run this in VS Code's integrated terminal:

.. code-block:: console

   python -m pip install -e . -e pipeline

Documentation dependencies are optional:

.. code-block:: console

   python -m pip install -r docs/requirements.txt

Python 3.10 receives the compatible Sphinx 8.1 line; newer Python versions use
Sphinx 8.2. This distinction affects contributors only—the installed atlas has
no Sphinx dependency.

Install the built wheel offline
-------------------------------

Test the exact release artifact without consulting a package index:

.. code-block:: console

   python -m pip install --no-index --no-deps dist/pyworldatlas-0.2.0-py3-none-any.whl

Verify the installation
-----------------------

.. doctest::

   >>> import pyworldatlas
   >>> pyworldatlas.__version__
   '0.2.0'
   >>> from pyworldatlas import Atlas
   >>> with Atlas() as atlas:
   ...     print(atlas.country("DO").capital.name)
   Santo Domingo
