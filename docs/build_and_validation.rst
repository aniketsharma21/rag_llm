Build & Validation
===================

This guide covers building the Sphinx documentation and running automated checks locally.

Prerequisites
-------------

* Python environment with ``sphinx`` and extensions installed. Add the following to your environment if missing:

  .. code-block:: bash

     pip install sphinx sphinxcontrib-mermaid sphinx-rtd-theme

* (Optional) Node.js toolchain for frontend builds and `pytest` for backend tests (see :doc:`testing`).

Building HTML Docs
------------------

From the project root, run:

.. code-block:: bash

   sphinx-build -b html docs/ docs/_build/html

Artifacts will be generated under ``docs/_build/html``. Open ``index.html`` in a browser to review.

Live Preview
------------

For iterative authoring, install ``sphinx-autobuild``:

.. code-block:: bash

   pip install sphinx-autobuild
   sphinx-autobuild docs/ docs/_build/html

This serves the docs locally with hot reloading on file changes.

Quality Gates
-------------

1. **Warnings as errors** – Enable ``-W`` to fail the build on warnings:

   .. code-block:: bash

      sphinx-build -b html -W docs/ docs/_build/html

2. **Link checking** – Validate external links:

   .. code-block:: bash

      sphinx-build -b linkcheck docs/ docs/_build/linkcheck

3. **Doctest** – Run embedded Python doctests (if added):

   .. code-block:: bash

      sphinx-build -b doctest docs/ docs/_build/doctest

Integrate these steps into CI pipelines alongside `pytest` to ensure documentation stays accurate and free of build regressions.
