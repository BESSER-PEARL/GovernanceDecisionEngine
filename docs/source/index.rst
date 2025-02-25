BESSER Governance Engine
========================

.. toctree::
   :maxdepth: 1
   :hidden:

   quickstart
   wiki
   examples
   release_notes
   api



The `BESSER Governance Engine (BGE) <https://github.com/BESSER-PEARL/BESSER-Governance-Engine>`_ is part of the
MOSAICO European project and integrated in the BESSER (Building Better Smart Software Faster) project at the
Luxembourg Institute of Science and Technology (LIST).
It aims at providing a way to enforce governance policies in the collaboration of human-agent and AI-agent during
the complete lifcycle of software.

Quickstart
----------

Requirements
~~~~~~~~~~~~

- Python 3.11
- Recommended: Create a virtual environment
  (e.g. `venv <https://docs.python.org/3/library/venv.html>`_,
  `conda <https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_)
- Install the `package <https://pypi.org/project/besser-governance-engine/>`_:

.. code:: bash

    pip install besser-governance-engine

This command will install the base package with its dependencies.

If you cloned the repository, you can install the dependencies by referencing to the requirements files:

.. code:: bash

    pip install -r requirements.txt


Where to start?
~~~~~~~~~~~~~~~

👉 Check out the :doc:`quickstart` tutorial. You will learn how simple it can be!

👉 Dive into the :doc:`wiki` to better understand the mechanism of policies enforcement.

Examples
--------------

- :doc:`examples/PR_merger`: Simple example of a majority rule to merge a pull request on github
