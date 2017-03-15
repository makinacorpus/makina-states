Tests & Quality Assurance
=========================
This will run:

    - unit tests
    - linters
    - install all states


See `travis test helper <https://github.com/makinacorpus/makina-states/blob/master/_scripts/travis_test.sh>`_
as an entry point to launch the tests on your environment.

Basically, it use nosetests via a custom salt module: `mc_test <https://github.com/makinacorpus/makina-states/blob/master/mc_states/modules/mc_test.py>`_

