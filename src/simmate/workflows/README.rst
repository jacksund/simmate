Simmate Workflows
-----------------

This module brings together all predefined workflows and organizes them by application for convenience.


Usage
-----

`Tutorials 01-05`_ will teach you how to run workflows and access their results. But as a review:

.. code-block:: python

    from simmate.workflows.all import energy_mit
    
    # runs the workflow and returns a status
    status = energy_mit.run(structure=...)
    
    # gives the DatabaseTable where ALL results are stored
    energy_mit.result_table
    
.. _Tutorials 01-05: https://github.com/jacksund/simmate/tree/main/tutorials


Location of Each Workflow's Source-code
--------------------------------

The code that defines these workflows and configures their settings are located in the corresponding ``simmate.calculators`` module. We make workflows accessible here because users often want to search for workflows by application -- not by their calculator name. For example, a structure relaxation that uses VASP under MIT project settings can be imported with...

.. code-block:: python

    from simmate.workflows.relaxation.all import relaxation_mit

Alternatively, this same workflow could have been imported with...

.. code-block:: python

    from simmate.calculators.vasp.workflows.relaxation.all import relaxation_mit
