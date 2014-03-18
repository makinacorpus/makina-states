{% set salts = salt['mc_salt.settings']() %}
{% set log = salts.msr+'/unittest.log' %}
include:
  -  makina-states.tests.base

unittest-makinastates-tests:
  cmd.run:
    - require_in:
      - file: markok
    - require:
      - file: removeok
    - name: |
            ./bin/test -s -v -i mc_states.tests 2>&1 > {{log}};
            ret=$?;
            cat {{log}};
            exit $ret
    - cwd: {{salts.msr}}
