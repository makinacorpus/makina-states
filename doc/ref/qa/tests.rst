Tests & Quality Assurance
=========================
This will run:

    - unit tests
    - linters
    - install all states

For this reason, run those states only a box that you ll trash afterwards

On a provisionned box, run::

    ./boot-salt.sh -C -s -S --tests

It will run all the sls found in ``makina-states.tests``.


